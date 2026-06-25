"""CamoFox source - stealth browser for career pages and JS-heavy SPAs."""

import json
import re
import time
import random
import urllib.request
import urllib.error
from sources.utils import ok_title

BASE = "http://127.0.0.1:9377"
AUTH = "Authorization: Bearer camofox-secret-2026"
USER_ID = "careersweep"


def _headers():
    return {"Authorization": AUTH, "Content-Type": "application/json"}


def _api(method, path, body=None):
    """Make API call to CamoFox."""
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def create_tab(url, session_key="sweep"):
    """Create a browser tab."""
    result = _api("POST", "/tabs", {
        "userId": USER_ID,
        "sessionKey": session_key,
        "url": url,
        "timeout": 15,
    })
    return result.get("tabId")


def wait_tab(tab_id):
    """Wait for page to load."""
    return _api("POST", f"/tabs/{tab_id}/wait", {"userId": USER_ID})


def evaluate(tab_id, expression):
    """Execute JS in page context."""
    return _api("POST", f"/tabs/{tab_id}/evaluate", {
        "userId": USER_ID,
        "expression": expression,
    })


def close_tab(tab_id):
    """Close a tab."""
    return _api("DELETE", f"/tabs/{tab_id}", {"userId": USER_ID})


def cleanup():
    """Delete all sessions for this user."""
    return _api("DELETE", f"/sessions/{USER_ID}")


def scrape_page(url, company_name, session_key=None):
    """Scrape a page for IT Manager/Director roles."""
    results = []
    if not session_key:
        session_key = f"career-{company_name.lower().replace(' ', '-')[:20]}"
    try:
        tab_id = create_tab(url, session_key)
        if not tab_id:
            return results
        time.sleep(5)
        wait_tab(tab_id)

        # Get full page text
        r = evaluate(tab_id, "document.body.innerText")
        text = r.get("result", "")
        if text and isinstance(text, str):
            for kw in ["manager", "director", "head", "infrastructure", "operations"]:
                for m in re.finditer(
                    r'([^\n]{0,60}' + re.escape(kw) + r'[^\n]{0,60})',
                    text, re.I
                ):
                    context = m.group(1).strip()
                    if ok_title(context):
                        results.append({
                            "company": company_name,
                            "title": context[:120],
                            "location": "Unlisted",
                            "url": url,
                            "source": f"camofox:{company_name}",
                        })

        # Also try link extraction
        r2 = evaluate(tab_id, """
        (function() {
            var links = [];
            document.querySelectorAll('a[href]').forEach(function(a) {
                var text = a.innerText.trim();
                if (text.length > 5 && text.length < 200) {
                    links.push({title: text, url: a.href});
                }
            });
            return JSON.stringify(links.slice(0, 200));
        })()
        """)
        raw = r2.get("result", "[]")
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            for item in data:
                title = item.get("title", "")
                if ok_title(title):
                    results.append({
                        "company": company_name,
                        "title": title[:120],
                        "location": "Unlisted",
                        "url": item.get("url", ""),
                        "source": f"camofox:{company_name}",
                    })
        except:
            pass

        close_tab(tab_id)
    except Exception:
        pass
    finally:
        try:
            cleanup()
        except:
            pass

    return results


def search_linkedin(queries):
    """Search LinkedIn Jobs with authenticated CamoFox session."""
    results = []
    try:
        # Login flow
        tab_id = create_tab("https://www.linkedin.com/login", "linkedin-login")
        if not tab_id:
            return results
        time.sleep(8)

        # Fill credentials via native setter
        login_js = """
        (function() {
            var ns = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            var email = document.querySelector('input[type="email"]');
            var pass = document.querySelector('input[type="password"]');
            if (!email || !pass) return 'FORM_MISSING';
            email.focus(); ns.call(email, 'freemancurtisd@gmail.com');
            email.dispatchEvent(new Event('input', {bubbles: true}));
            email.dispatchEvent(new Event('change', {bubbles: true}));
            email.blur();
            pass.focus(); ns.call(pass, '11aaxx2wr');
            pass.dispatchEvent(new Event('input', {bubbles: true}));
            pass.dispatchEvent(new Event('change', {bubbles: true}));
            pass.blur();
            var buttons = document.querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].innerText.trim() === 'Sign in') {
                    buttons[j].click();
                    return 'submitted';
                }
            }
            return 'NO_SUBMIT';
        })()
        """
        evaluate(tab_id, login_js)
        time.sleep(8)

        # Check if CAPTCHA
        r = evaluate(tab_id, "window.location.href")
        current_url = r.get("result", "")
        if "/checkpoint" in current_url or "/login" in current_url:
            close_tab(tab_id)
            cleanup()
            return results

        # Search jobs
        for query in queries:
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}&location=United%20States&f_TPR=r604800&f_WT=2"
            evaluate(tab_id, f"window.location.href = '{search_url}'")
            time.sleep(5)

            extract_js = """
            (function() {
                var jobs = [];
                var cards = document.querySelectorAll('.job-card-container, .jobs-search-results__list-item, .scaffold-layout__list-item');
                for (var i = 0; i < Math.min(cards.length, 25); i++) {
                    var card = cards[i];
                    var titleEl = card.querySelector('.job-card-list__title, .artdeco-entity-lockup__title, a[href*="/jobs/view/"]');
                    var companyEl = card.querySelector('.job-card-container__primary-description, .artdeco-entity-lockup__subtitle');
                    var locationEl = card.querySelector('.job-card-container__metadata-item, .artdeco-entity-lockup__caption');
                    var linkEl = card.querySelector('a[href*="/jobs/view/"]');
                    if (titleEl) {
                        jobs.push({
                            title: titleEl.innerText.trim(),
                            company: companyEl ? companyEl.innerText.trim() : '',
                            location: locationEl ? locationEl.innerText.trim() : '',
                            url: linkEl ? linkEl.href : ''
                        });
                    }
                }
                return JSON.stringify(jobs);
            })()
            """
            r = evaluate(tab_id, extract_js)
            raw = r.get("result", "[]")
            try:
                jobs = json.loads(raw) if isinstance(raw, str) else raw
            except:
                jobs = []

            for j in jobs:
                title = j.get("title", "")
                if ok_title(title):
                    results.append({
                        "company": j.get("company", "LinkedIn"),
                        "title": title,
                        "location": j.get("location", "Unlisted"),
                        "url": j.get("url", ""),
                        "source": "linkedin",
                    })

        close_tab(tab_id)
    except Exception:
        pass
    finally:
        try:
            cleanup()
        except:
            pass

    return results


# CamoFox configs
CAMOFOX_LINKEDIN_QUERIES = [
    "IT Manager",
    "IT Director",
    "Senior IT Manager",
    "IT Operations Manager",
    "Infrastructure Manager",
]

# Career pages from the master list - Vegas local + major employers
CAMOFOX_CAREER_PAGES = [
    ("https://careers.mgmresorts.com", "MGM Resorts"),
    ("https://careers.caesars.com", "Caesars Entertainment"),
    ("https://careers.wynnresorts.com", "Wynn Resorts"),
    ("https://www.stationcasinos.com/careers", "Station Casinos"),
    ("https://www.clarkcountynv.gov/government/departments/human_resources/employment.php", "Clark County"),
    ("https://www.lasvegasnevada.gov/Government/Departments/Human-Resources/Employment", "City of Las Vegas"),
    ("https://www.usajobs.gov", "USAJobs Federal"),
    ("https://www.governmentjobs.com/careers?keywords=IT+Manager&location=Las+Vegas", "GovernmentJobs NEOGOV"),
    # Tech companies with HTML career pages
    ("https://careers.google.com", "Google"),
    ("https://www.metacareers.com", "Meta"),
    ("https://careers.apple.com", "Apple"),
    ("https://www.amazon.jobs", "Amazon"),
    ("https://careers.microsoft.com", "Microsoft"),
    ("https://www.salesforce.com/company/careers", "Salesforce"),
    # High-paying remote specialists
    ("https://remote100k.com", "Remote100K"),
    ("https://www.flexjobs.com", "FlexJobs"),
    ("https://remote.co", "Remote.co"),
    ("https://www.virtualvocations.com", "Virtual Vocations"),
    ("https://www.workingnomads.com", "Working Nomads"),
    ("https://jobspresso.co", "Jobspresso"),
    ("https://justremote.co", "JustRemote"),
    ("https://nodesk.co", "NoDesk"),
    ("https://remoterocketship.com", "Remote Rocketship"),
    # Executive
    ("https://www.theladders.com", "The Ladders"),
    ("https://www.ivyexec.com", "Ivy Exec"),
    ("https://www.6figurejobs.com", "6FigureJobs"),
    # AI/ML niche
    ("https://ai-jobs.net", "AI-Jobs.net"),
    ("https://mljobs.io", "MLJobs.io"),
    # Startup
    ("https://wellfound.com", "Wellfound"),
    ("https://www.workatastartup.com", "YC Work at Startup"),
    ("https://startup.jobs", "Startup Jobs"),
]


def scan_camofox_boards():
    """Scan all CamoFox-protected boards."""
    all_results = []
    all_errors = []

    # LinkedIn (authenticated)
    try:
        results = search_linkedin(CAMOFOX_LINKEDIN_QUERIES)
        all_results.extend(results)
    except Exception as e:
        all_errors.append(f"linkedin: {e}")

    # Career pages
    for url, company in CAMOFOX_CAREER_PAGES:
        try:
            results = scrape_page(url, company)
            all_results.extend(results)
        except Exception as e:
            all_errors.append(f"camofox:{company}: {e}")

    return all_results, all_errors
