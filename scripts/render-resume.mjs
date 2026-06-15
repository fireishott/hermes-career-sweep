#!/usr/bin/env node
import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { renderHtmlToPdf } from '../generate-pdf.mjs';

function esc(v = '') {
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function fileSlug(s = '') {
  return String(s)
    .replace(/&/g, ' and ')
    .replace(/[^A-Za-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'Resume';
}

function outputBaseName(resume, job) {
  const name = fileSlug(resume?.contact?.name || 'Candidate').replaceAll('-', '');
  const parts = [job?.company, job?.title].filter(Boolean).map(fileSlug);
  return `${name}_${parts.join('_') || 'Resume'}_Resume`;
}

function usage() {
  console.error('Usage: node scripts/render-resume.mjs --resume resume.json --out-dir <folder> [--job job.json] [--format letter]');
  process.exit(2);
}

function arg(name, fallback = null) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function list(items = []) {
  return (items || []).filter(Boolean).map(x => `<li>${esc(x)}</li>`).join('\n');
}

function renderSkills(skills = []) {
  if (!Array.isArray(skills)) return '';
  return skills.map(group => {
    if (typeof group === 'string') return `<li>${esc(group)}</li>`;
    const items = Array.isArray(group.items) ? group.items.join(' • ') : '';
    return `<li><strong>${esc(group.category || 'Skills')}:</strong> ${esc(items)}</li>`;
  }).join('\n');
}

function renderExperience(exp = []) {
  return exp.map(role => `
    <section class="role">
      <div class="role-head">
        <div><strong>${esc(role.title)}</strong><span>${esc(role.company)}</span></div>
        <div class="dates">${esc([role.start, role.end].filter(Boolean).join(' - '))}</div>
      </div>
      <div class="location">${esc(role.location || '')}</div>
      <ul>${list(role.bullets || [])}</ul>
    </section>`).join('\n');
}

function renderEducation(edu = []) {
  return edu.map(e => `<li><strong>${esc(e.degree || e.school || '')}</strong>${e.major ? ` — ${esc(e.major)}` : ''}${e.school ? `, ${esc(e.school)}` : ''}${e.year ? ` (${esc(e.year)})` : ''}</li>`).join('\n');
}

function htmlDoc(resume, job) {
  const c = resume.contact || {};
  const title = c.title || resume.target_title || job?.title || 'IT Operations & AI Enablement Leader';
  const accent = resume.meta?.accent_color || '#0acf83';
  return `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>${esc(c.name || 'Candidate Name')} Resume</title>
<style>
  @page { size: Letter; margin: 0.55in; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; color: #121417; margin: 0; line-height: 1.28; font-size: 10.2pt; }
  header { border-bottom: 3px solid ${accent}; padding-bottom: 10px; margin-bottom: 12px; }
  h1 { margin: 0; font-size: 24pt; letter-spacing: -0.04em; }
  .title { font-size: 12pt; font-weight: 700; margin-top: 2px; color: #263238; }
  .contact, .target { margin-top: 5px; color: #424b54; font-size: 9pt; }
  h2 { font-size: 10.6pt; letter-spacing: .08em; text-transform: uppercase; margin: 13px 0 5px; color: #111; border-bottom: 1px solid #d7dde3; padding-bottom: 2px; }
  p { margin: 0 0 6px; }
  ul { margin: 4px 0 0 16px; padding: 0; }
  li { margin: 0 0 3px; }
  .role { margin-bottom: 8px; break-inside: avoid; }
  .role-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
  .role-head strong { font-size: 10.3pt; }
  .role-head span { display: block; color: #28313a; font-weight: 600; }
  .dates { white-space: nowrap; color: #4f5b66; font-size: 9pt; }
  .location { color: #69737d; font-size: 8.8pt; margin-top: 1px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }
</style>
</head>
<body>
<header>
  <h1>${esc(c.name || 'Candidate Name')}</h1>
  <div class="title">${esc(title)}</div>
  <div class="contact">${esc([c.location, c.email, c.phone, c.website, c.linkedin].filter(Boolean).join(' | '))}</div>
</header>

<h2>Professional Summary</h2>
<p>${esc(resume.summary || '')}</p>

<h2>Core Skills</h2>
<ul>${renderSkills(resume.skills || [])}</ul>

<h2>Professional Experience</h2>
${renderExperience(resume.experience || [])}

<div class="grid">
  <section>
    <h2>Education & Leadership</h2>
    <ul>${renderEducation(resume.education || [])}</ul>
  </section>
  <section>
    ${(resume.certifications || []).length ? `<h2>Certifications</h2><ul>${list(resume.certifications)}</ul>` : ''}
    ${(resume.projects || []).length ? `<h2>Selected Projects</h2><ul>${list(resume.projects.map(p => typeof p === 'string' ? p : `${p.name}: ${p.description || ''}`))}</ul>` : ''}
  </section>
</div>
</body>
</html>`;
}

const resumePath = arg('resume');
const outDir = arg('out-dir');
const jobPath = arg('job');
const format = arg('format', 'letter');
if (!resumePath || !outDir) usage();

const resume = JSON.parse(await readFile(resumePath, 'utf8'));
const job = jobPath && existsSync(jobPath) ? JSON.parse(await readFile(jobPath, 'utf8')) : null;
await mkdir(outDir, { recursive: true });
const html = htmlDoc(resume, job);
const baseName = outputBaseName(resume, job);
const htmlPath = path.join(outDir, `${baseName}.html`);
const pdfPath = path.join(outDir, `${baseName}.pdf`);
await writeFile(htmlPath, html);
const result = await renderHtmlToPdf(html, pdfPath, { format, baseDir: outDir });
const manifest = {
  generated_at: new Date().toISOString(),
  resume_json: path.resolve(resumePath),
  job_json: jobPath ? path.resolve(jobPath) : null,
  html: htmlPath,
  pdf: pdfPath,
  size: result.size,
  page_count: result.pageCount,
};
await writeFile(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify(manifest, null, 2));
