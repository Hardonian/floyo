# Floyo

**Discover hidden connections in your workflow. Automate what you didn't know could be automated.**

[![Deployment Status](https://img.shields.io/badge/deployment-vercel-blue)](https://vercel.com)
[![Database](https://img.shields.io/badge/database-supabase-green)](https://supabase.com)
[![Framework](https://img.shields.io/badge/framework-nextjs-black)](https://nextjs.org)

---

## What is Floyo?

Floyo watches how you work—the files you open, the scripts you run, the tools you use—and finds patterns you didn't notice. Then it suggests concrete, actionable integrations that can automate the repetitive parts of your workflow.

Think of it as a personal assistant that learns your habits and proposes smart connections between the tools you already use.

### The Problem

You're juggling multiple tools, scripts, and files every day. You know there's probably a way to automate some of it, but:

- You don't have time to research every possible integration
- You're not sure which automations would actually help
- You don't want to set up complex workflows that break
- You want suggestions based on *your actual work*, not generic examples

### The Solution

Floyo runs quietly in the background, learning your patterns. When it spots an opportunity—like "you always run this Python script and then manually upload the output to Dropbox"—it suggests a simple integration with actual code you can use.

**No guessing. No generic advice. Just real suggestions based on what you actually do.**

---

## Key Features

### 🎯 Pattern Recognition
Floyo tracks file usage, script executions, and tool interactions to identify your unique workflow patterns.

### 💡 Intelligent Suggestions
Get concrete integration suggestions with sample code tailored to your actual files and workflows.

### 🔒 Privacy-First
All tracking happens locally. Your data stays on your machine unless you choose to sync it.

### ⚡ Real-Time Monitoring
Watch your file system in real-time and get instant insights into how you work.

### 🔗 Relationship Mapping
See how files, scripts, and tools connect in your workflow—discover dependencies you didn't know existed.

### 📊 Usage Analytics
Understand your work patterns with temporal analysis and usage statistics.

---

## Real-World Use Cases

### The Data Analyst
Sarah runs Python scripts to process CSV files, then manually emails the results. Floyo detects this pattern and suggests automating the email step with a simple integration.

**Outcome:** Sarah saves 30 minutes per day and never forgets to send reports.

### The Developer
Mike frequently edits TypeScript files, runs tests, and then checks deployment logs. Floyo suggests connecting these steps into an automated workflow.

**Outcome:** Mike catches deployment issues faster and reduces context switching.

### The Content Creator
Emma writes markdown files, converts them to PDFs, and uploads to a cloud service. Floyo spots this pattern and suggests a one-click automation.

**Outcome:** Emma publishes content 3x faster with zero manual steps.

### The Researcher
David analyzes data files, generates visualizations, and shares them via Slack. Floyo proposes connecting these tools automatically.

**Outcome:** David's team gets insights faster, and he focuses on analysis instead of file management.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Floyo System                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │   Frontend   │◄─────►│   Backend    │◄─────►│ Database │ │
│  │  (Next.js)   │      │  (FastAPI)   │      │(Supabase) │ │
│  └──────────────┘      └──────────────┘      └──────────┘ │
│         │                     │                            │
│         │                     │                            │
│         ▼                     ▼                            │
│  ┌──────────────┐      ┌──────────────┐                  │
│  │ File Watcher │      │  Pattern     │                  │
│  │  (Local)     │      │  Analyzer    │                  │
│  └──────────────┘      └──────────────┘                  │
│         │                     │                            │
│         └─────────────────────┘                            │
│                    │                                        │
│                    ▼                                        │
│         ┌──────────────────────┐                          │
│         │ Integration Suggester │                          │
│         └──────────────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend:** Next.js 14+ (App Router), React, TypeScript, Tailwind CSS
- **Backend:** Python (FastAPI), SQLAlchemy
- **Database:** PostgreSQL (via Supabase)
- **Authentication:** Supabase Auth
- **Deployment:** Vercel (frontend), Supabase (database)
- **CI/CD:** GitHub Actions

---

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for backend)
- PostgreSQL (via Supabase)
- Vercel account (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd floyo-monorepo
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   # Fill in values from Supabase Dashboard
   ```

3. **Install dependencies**
   ```bash
   npm install
   cd frontend && npm install
   cd ../backend && pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Link Supabase project
   supabase link --project-ref <your-project-ref>
   
   # Run migrations
   supabase db push
   
   # Generate Prisma client
   npm run prisma:generate
   ```

5. **Start development servers**
   ```bash
   # Frontend (Next.js) - Terminal 1
   cd frontend && npm run dev
   
   # Backend (Python) - Terminal 2
   cd backend && python -m uvicorn main:app --reload
   ```

6. **Open your browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Project Structure

```
floyo-monorepo/
├── frontend/              # Next.js frontend application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and helpers
│   └── public/           # Static assets
│
├── backend/              # Python FastAPI backend
│   ├── api/              # API route handlers
│   ├── services/         # Business logic
│   ├── models/           # Database models
│   └── jobs/             # Background jobs
│
├── floyo/                # Core tracking library (CLI tool)
│   ├── tracker.py        # Usage pattern tracking
│   ├── suggester.py      # Integration suggestions
│   ├── watcher.py        # File system monitoring
│   └── cli.py            # Command-line interface
│
├── supabase/             # Database migrations and functions
│   ├── migrations/       # SQL migration files
│   └── functions/        # Edge functions
│
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
│
├── scripts/              # Utility scripts
├── docs/                 # Documentation
└── infra/                # Infrastructure as code
```

---

## Screenshots & Demos

> **Coming Soon:** Screenshots of the dashboard, suggestion interface, and workflow visualization.

**Want to see Floyo in action?** Check out our [demo video](#) (coming soon) or [try it yourself](#quick-start).

---

## Development

### Available Scripts

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Formatting
npm run format

# Testing
npm run test              # Run all tests
npm run test:coverage     # Generate coverage report
npm run test:e2e          # Run end-to-end tests

# Build
npm run build

# Database
npm run prisma:generate   # Generate Prisma client
npm run prisma:migrate    # Run migrations
npm run prisma:studio     # Open Prisma Studio
```

### Running Tests Locally

```bash
# Python tests
cd backend
pytest tests/unit/ -v

# TypeScript tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

See [CI Configuration](.github/workflows/ci.yml) for the full test suite that runs on every commit.

---

## Documentation

### YC Readiness
- **[🚀 Quick Start](./yc/QUICK_START.md)** - One-command setup: `npm run yc:setup-complete`
- **[YC Readiness Overview](./yc/REPO_ORIENTATION.md)** - Quick orientation for YC partners and investors
- **[YC Interview Cheat Sheet](./yc/YC_INTERVIEW_CHEATSHEET.md)** - Interview prep reference
- **[Full YC Documentation](./yc/)** - Complete YC readiness package (product, metrics, distribution, tech)
- **[✅ Status: 100% Complete](./yc/ALL_COMPLETE.md)** - All gaps addressed, all next steps automated

### Getting Started
- **[Local Development Guide](./docs/local-dev.md)** - Complete setup instructions for local development
- **[Environment Variables](./docs/env-and-secrets.md)** - Environment variables and secrets management
- **[Stack Discovery](./docs/stack-discovery.md)** - Complete architecture and stack analysis

### Architecture & Strategy
- **[Backend Strategy](./docs/backend-strategy.md)** - Backend & database strategy (Supabase + Prisma)
- **[Frontend Hosting Strategy](./docs/frontend-hosting-strategy.md)** - Frontend hosting on Vercel
- **[CI/CD Overview](./docs/ci-overview.md)** - Complete CI/CD pipeline documentation

### Deployment & Operations
- **[Frontend Deployment](./docs/frontend-deploy-vercel-ci.md)** - Vercel deployment guide
- **[Database Migrations](./docs/supabase-migrations-ci.md)** - Supabase migrations guide

### Demo & Onboarding
- **[Demo Script](./docs/demo-script.md)** - Demo-ready guide for showcasing Floyo

### Audit & Reports
- **[Repository Audit Summary](./docs/REPO_AUDIT_SUMMARY.md)** - Complete audit report

### Legacy Documentation
- **[ENVIRONMENT.md](./ENVIRONMENT.md)** - Legacy environment variables reference
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System architecture and design
- **[API.md](./docs/API.md)** - API endpoint documentation
- **[WORKFLOW.md](./docs/WORKFLOW.md)** - Development workflow and guidelines

### Health Reports

- **[Schema Health Report](./reports/SCHEMA_HEALTH_REPORT.md)** - Database schema analysis
- **[Deployment Health Report](./reports/DEPLOYMENT_HEALTH_REPORT.md)** - Vercel deployment analysis
- **[Repo Integrity Report](./reports/REPO_INTEGRITY_REPORT.md)** - Code organization analysis

---

## Security

### Environment Variables

Never commit secrets to git. Use:
- `.env.local` for local development
- Vercel Environment Variables for production
- GitHub Secrets for CI/CD

See [ENVIRONMENT.md](./ENVIRONMENT.md) for complete variable reference.

### Security Best Practices

- ✅ All API routes authenticated
- ✅ Row Level Security (RLS) enabled on all tables
- ✅ Input validation on all endpoints
- ✅ Rate limiting configured
- ✅ CORS properly configured
- ✅ Security headers enabled

---

## CI/CD Overview

- **Frontend**: Deployed via GitHub Actions to Vercel (Preview for PRs, Production for `main`)
- **Database (Supabase)**: Migrations are applied via GitHub Actions using the Supabase CLI
- **No local CLI required**: Everything runs in GitHub Actions - no need to install Vercel or Supabase CLI locally

### Workflows

- **`frontend-deploy.yml`**: Primary frontend CI/CD workflow - runs quality checks and deploys to Vercel
- **`ci.yml`**: Main CI pipeline - lint, typecheck, tests, build
- **`supabase-migrate.yml`**: Database migrations workflow - applies Supabase migrations
- **`preview-pr.yml`**: Additional quality gates (Lighthouse, Pa11y) for PRs

See:
- [docs/frontend-deploy-vercel-ci.md](docs/frontend-deploy-vercel-ci.md) - Detailed frontend deployment guide
- [docs/ci-overview.md](docs/ci-overview.md) - Complete CI/CD pipeline documentation

---

## Deployment

### Vercel Deployment

**Automated via GitHub Actions** - No local CLI required!

1. **Set up GitHub Secrets** (one-time setup):
   - `VERCEL_TOKEN` - Get from [Vercel Dashboard → Tokens](https://vercel.com/account/tokens)
   - `VERCEL_ORG_ID` - Get from Vercel Dashboard → Organization Settings
   - `VERCEL_PROJECT_ID` - Get from Vercel Dashboard → Project Settings

2. **Set environment variables in Vercel Dashboard**:
   - Add all required variables from [ENVIRONMENT.md](./ENVIRONMENT.md)
   - Set different values for Production/Preview/Development

3. **Deploy**:
   - **Preview**: Create a pull request → automatically deploys preview environment
   - **Production**: Merge to `main` → automatically deploys to production

**See [docs/frontend-deploy-vercel-ci.md](docs/frontend-deploy-vercel-ci.md) for complete setup instructions.**

### Database Migrations

**Automated via GitHub Actions** - No local CLI required!

Migrations are applied automatically via the `supabase-migrate.yml` workflow when:
- Code is merged to `main` branch, or
- Manually triggered via GitHub Actions UI

**Required GitHub Secrets**:
- `SUPABASE_ACCESS_TOKEN` - Get from [Supabase Dashboard → Access Tokens](https://supabase.com/dashboard/account/tokens)
- `SUPABASE_PROJECT_REF` - Your Supabase project reference ID

**Local development** (optional):
```bash
# Create new migration
supabase migration new <migration-name>

# Apply migrations locally
supabase db push

# Check migration status
supabase db remote commit --dry-run
```

**See [docs/supabase-migrations-ci.md](docs/supabase-migrations-ci.md) for CI setup details.**

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests and linting**
   ```bash
   npm run test
   npm run lint
   npm run format
   ```
5. **Create a pull request**
6. **Ensure CI/CD passes**

See [WORKFLOW.md](./docs/WORKFLOW.md) for detailed workflow guidelines.

---

## License

See [LICENSE](./LICENSE) file for details.

---

## Support

- **Documentation:** See `/docs` directory
- **Issues:** Create an issue on [GitHub Issues](#)
- **Health Reports:** See `/reports` directory
- **Questions?** Open a discussion on [GitHub Discussions](#)

---

## Status

**Last Updated:** Auto-maintained by Autonomous Full-Stack Guardian

This repository is continuously monitored and maintained by autonomous systems to ensure:
- ✅ Environment variable alignment
- ✅ Schema accuracy
- ✅ Deployment success
- ✅ Code integrity
- ✅ Integration health

See health reports in `/reports` for current status.

---

## Star This Repo ⭐

If Floyo helps you discover and automate your workflow patterns, please consider giving us a star! It helps others discover the project and motivates us to keep improving.

---

**Built with ❤️ for developers who want to work smarter, not harder.**

---

## About

**Floyo** is built by **Scott Hardie**, Founder, CEO & Operator.

**Scott Hardie** brings 15+ years of experience helping businesses adopt SaaS tools (McGraw Hill, Pearson Education) and has recently built AI automation systems directly relevant to Floyo's target market: Hardonia OS (AI-driven Shopify commerce lab), PromptPilot (workflow automation framework), and Daily Intel Suite (agent-based insights). His combination of sales/enablement experience + recent AI automation work makes him uniquely qualified to build Floyo.

- **GitHub:** [shardie-github](https://github.com/shardie-github)
- **LinkedIn:** [/scottrmhardie](https://linkedin.com/in/scottrmhardie)
- **Email:** scottrmhardie@gmail.com

See `/yc/YC_TEAM_NOTES.md` for full founder background.

---

---

## Related Hardonia projects

<p align="center">
  <a href="https://aiautomatedsystems.ca"><img src="https://img.shields.io/badge/AI_Automated_Systems-Visit-0f766e?style=for-the-badge&logo=cloudflare" alt="AI Automated Systems" /></a>
  <a href="https://github.com/Hardonian/ollama-router"><img src="https://img.shields.io/badge/ollama--router-181717?style=for-the-badge&logo=github" alt="ollama-router" /></a>
  <a href="https://github.com/Hardonian/ai-lab-audit-api"><img src="https://img.shields.io/badge/ai--lab--audit--api-181717?style=for-the-badge&logo=github" alt="ai-lab-audit-api" /></a>
  <a href="https://github.com/Hardonian/ai-lab-command-center"><img src="https://img.shields.io/badge/command--center-181717?style=for-the-badge&logo=github" alt="ai-lab-command-center" /></a>
  <a href="https://github.com/Hardonian/storefront"><img src="https://img.shields.io/badge/storefront-181717?style=for-the-badge&logo=github" alt="storefront" /></a>
</p>

<p align="center"><strong>Part of the <a href="https://aiautomatedsystems.ca">Hardonia</a> open-source + services stack.</strong></p>

<p align="center">
  <a href="https://aiautomatedsystems.ca/p/repo-rescue-saas-audit"><img src="https://img.shields.io/badge/Get_a-SaaS_Repo_Rescue_Audit-635BFF?style=for-the-badge&logo=stripe&logoColor=white" alt="SaaS Repo Rescue Audit" /></a>
</p>

<details>
<summary>What this audit covers</summary>

A fixed-scope review of **auth, billing, RLS, and webhook** correctness — the bugs that cost you customers and chargebacks. Runs locally on your infrastructure. See the <a href="https://aiautomatedsystems.ca/p/repo-rescue-saas-audit">product page</a>.
</details>
