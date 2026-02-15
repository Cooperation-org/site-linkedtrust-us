# LinkedTrust.us Website — Claude Code Context

## Project Overview
This is the LinkedTrust.us marketing/portfolio website. Django 4.2, PostgreSQL, vanilla JS + CSS.
The site showcases LinkedTrust's services, portfolio of real projects, and verified trust badges.

## Quick Start
```bash
cd /opt/shared/repos/site-linkedtrust-us/New_website_code
python3 manage.py runserver 0.0.0.0:8000
```
Admin: http://localhost:8000/admin/ (admin/admin123)

### Serve under demos.linkedtrust.us/site-dev/
```bash
SCRIPT_NAME=/site-dev python3 manage.py runserver 0.0.0.0:8001
```
nginx is already configured to proxy `/site-dev/` to port 8001.

## Architecture

### Database
- **Shared PostgreSQL** at `10.0.0.100:5432`, user `cobox`, no password
- **Dev DB**: `linkedtrust_site_dev` (set `DJANGO_ENV=dev`, default)
- **Prod DB**: `linkedtrust_site_prod` (set `DJANGO_ENV=prod`)
- **IMPORTANT**: Always use semantic namespacing for any new databases: `linkedtrust_{purpose}_{env}`

### Key Models (`website/models.py`)
- `PortfolioProject` — portfolio items with slug, category, tech_tags, featured flag
- `CaseStudy` — OneToOne to Project (Problem → Solution → Result format)
- `Testimonial` — client quotes with optional `linked_claim_id` for badge embedding
- `ServicePackage` — service offerings with M2M to projects, pricing, slug
- `TeamMember` — existing team profiles with hourly rate and modal detail

### URL Structure (all deep-linkable)
```
/                           Homepage (hero + badges + featured work + services)
/about/                     About us
/work/                      Portfolio grid (filterable by category)
/work/<slug>/               Project detail page
/work/<slug>/case-study/    Case study for a project
/services/                  Service packages overview
/services/<slug>/           Service detail with related projects
/team/                      Team grid with modal detail
/contact/                   Google Form embed + contact info
```

### Design System
- **CSS**: `static/css/site.css` — single file, "Tech Meets Human" theme
- **Colors**: Light base (#FAFAF8) + dark tech sections (#0f1117) + cyan brand (#00B2E5) + purple accent (#667eea)
- **Fonts**: Montserrat (body), JetBrains Mono (tech labels, `.mono` class)
- **Images**: Sharp corners (border-radius: 0) on all photos for "real" feel
- **Templates**: `base.html` → includes `navbar.html` + `footer.html`

### Badge Web Component
The `<linked-badge>` web component loads from `https://linkedtrust.us/badge.js`.
Source: `/opt/shared/repos/trust_claim/public/badge.js`
Usage in templates:
```html
<linked-badge claim-id="124443" theme="dark"></linked-badge>
<linked-badge claim-id="124443" theme="light" compact></linked-badge>
```
Attributes: `claim-id` (required), `theme` (light/dark), `compact` (flag), `api-base` (override)

### Management Commands
```bash
python3 manage.py seed_portfolio          # Seed projects + services
python3 manage.py seed_portfolio --clear  # Clear and re-seed
```

## Files Changed in This Revamp

### New/Rewritten
- `static/css/site.css` — full design system
- `website/templates/base.html` — new base with JetBrains Mono + site.css
- `website/templates/navbar.html` — 5-item nav with mobile hamburger
- `website/templates/footer.html` — 3-column footer
- `website/templates/index.html` — homepage (hero + badges + services + portfolio)
- `website/templates/about.html` — about page
- `website/templates/team.html` — team grid with new card design
- `website/templates/contact.html` — two-column layout with Google Form
- `website/templates/work_list.html` — portfolio grid with category filters
- `website/templates/work_detail.html` — project detail with case study + testimonials
- `website/templates/case_study.html` — extends work_detail.html
- `website/templates/services.html` — services overview grid
- `website/templates/service_detail.html` — service detail with related projects
- `website/models.py` — added PortfolioProject, CaseStudy, Testimonial, ServicePackage
- `website/admin.py` — registered all models with inlines and filters
- `website/views.py` — added work_list, work_detail, case_study, service_detail views
- `website/urls.py` — new deep-linkable URL patterns
- `website/management/commands/seed_portfolio.py` — data seeding command
- `linkedtrust/settings.py` — PostgreSQL config, FORCE_SCRIPT_NAME support

### Old files still present but unused
- `static/css/main.css`, `static/css/styles.css`, `static/css/responsive.css` — old dark-theme CSS

## What Needs Doing Next

### Priority 1: Content (via Django admin)
1. Add screenshots/thumbnails for each portfolio project (upload in admin)
2. Write 2-3 case studies (StreetWell, AZ-Sunshine, Accentrics are good candidates)
3. Add real testimonials with `linked_claim_id` values from the trust graph
4. Add team member photos if missing

### Priority 2: Polish
1. Review and adjust homepage copy
2. Test on mobile (check at 375px, 768px)
3. Update "Trusted By" section with actual logo images (currently text placeholders)
4. Add meta descriptions and OG tags for social sharing
5. Review the press.html and privacy.html templates (not yet updated to new design)

### Priority 3: Production
1. Generate a proper SECRET_KEY
2. Set DEBUG=False for prod
3. Run `python3 manage.py collectstatic`
4. Set up gunicorn + systemd service
5. Point linkedtrust.us DNS/nginx at the new site

## Design Gallery
Static mockups at `/var/www/html/site-gallery/` (demos.linkedtrust.us/site-gallery/)
Current direction: Option C "Tech Meets Human" — light base with dark tech sections.
Golda: "lean into the contrast of tech + human", "center the real things"
