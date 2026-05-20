# Workload Allocation

## Group Members

| Name | GitHub Username | Email |
|------|----------------|-------|
| Kai-Hsiang Chuang | krischuang | kris.kh.chuang@gmail.com |
| Shelly Huang | ShellyHZX | shellylove1119@gmail.com |
| Dequan Xu | docccdol | docccdol@outlook.com |

---

## Responsibility Overview

| Area | Kai-Hsiang Chuang | Shelly Huang | Dequan Xu |
|------|:-----------------:|:------------:|:---------:|
| Backend — Auth & Security | ✅ | | |
| Backend — Article CRUD | | ✅ | |
| Backend — Admin Management | ✅ | | |
| Backend — AI Summary | ✅ | | |
| Backend — Bookmark CRUD | ✅ | | |
| Backend — Infrastructure & CI/CD | ✅ | | |
| Frontend — App Architecture & Styling | | | ✅ |
| Frontend — Admin Panel (articles + users) | | | ✅ |
| Frontend — Article Pages (listing + detail) | | | ✅ |
| Frontend — Article Detail UX Enhancements | | ✅ | |
| Frontend — Dark Mode | | ✅ | |
| Frontend — Recently Viewed Articles | | ✅ | |
| Frontend — Auth Pages (sign-in + sign-up) | ✅ | | |
| Frontend — Profile & Bookmarks | ✅ | ✅ | |
| Frontend — Password Reset Flow | ✅ | | |
| Frontend — AI Summary Panel | ✅ | | |
| Frontend — BFF Proxy Routes | ✅ | | ✅ |
| Frontend — CI/CD & Deployment | ✅ | | |

---

## Kai-Hsiang Chuang — Backend & Frontend Auth/Profile/AI

### Backend (`IP_Group_Assignment_Backend/`)

| File | Description |
|------|-------------|
| `app/config.py` | Pydantic settings — reads all environment variables |
| `app/database.py` | Beanie/MongoDB connection and teardown |
| `app/dependencies.py` | FastAPI `get_current_user` and `require_admin` dependencies |
| `app/keys.py` | RSA key-pair loading from PEM files |
| `app/main.py` | FastAPI app factory, CORS, and router registration |
| `app/models/user.py` | `User` Beanie document with role and hashed-password fields |
| `app/models/counter.py` | Auto-increment counter document for sequential IDs |
| `app/models/password_reset.py` | `PasswordResetToken` document for OTP-based reset |
| `app/models/bookmark.py` | `Bookmark` document linking user to article with optional note |
| `app/routers/auth.py` | Auth endpoints: sign-up, sign-in, public-key, forgot-password, validate-reset-token, reset-password, change-password |
| `app/routers/admin.py` | Admin-only endpoints: list/get/update/delete users |
| `app/routers/ai_tools.py` | Async AI summary job: create, poll status, store result via OpenRouter |
| `app/routers/bookmark.py` | Bookmark CRUD: create, list (with article title join), update note, delete |
| `app/utils/email.py` | Async HTML email sender (aiosmtplib) for OTP delivery |
| `app/utils/rsa_crypto.py` | RSA-PKCS1v15 decryption helper for password in transit |
| `app/utils/turnstile.py` | Cloudflare Turnstile server-side verification |
| `requirements.txt` | Python dependency list |
| `.github/workflow/deploy.yml` | Backend CI/CD pipeline (auto-deploy to AWS EC2) |
| `README.md` | Backend setup guide, API overview, folder structure |

### Frontend (`IP_Group_Assignment_Frontend/`)

| File | Description |
|------|-------------|
| `actions/auth.ts` | Server actions: `signInWithPassword`, `signUpWithEmail`, `signOut` with RSA-encrypted passwords |
| `actions/bookmarks.ts` | Server actions: `listBookmarksAction`, `createBookmarkAction`, `updateBookmarkAction`, `deleteBookmarkAction` |
| `actions/password-reset.ts` | Server actions: `forgotPassword`, `validateResetToken`, `resetPassword`, `changePassword` |
| `app/sign-in/page.tsx` | Sign-in page with Turnstile, redirect-after-login, forgot-password trigger |
| `app/sign-up/page.tsx` | Sign-up page with Turnstile, password strength meter, confirm-password check |
| `app/profile/page.tsx` | Profile page: edit name/email, change password, manage bookmarks (co-authored with Shelly) |
| `app/forgot-password/page.tsx` | Standalone forgot-password page (3-step: email → OTP → new password) |
| `app/articles/[id]/page.tsx` | AI summary panel with real-time job polling and animated progress bar (co-authored with Dequan and Shelly) |
| `app/bff/bookmarks/route.ts` | BFF GET proxy for bookmarks (returns `[]` when unauthenticated) |
| `app/bff/ai-tools/summary/jobs/[job_id]/route.ts` | BFF proxy for AI job polling |
| `components/ForgotPasswordModal.tsx` | Inline 3-step OTP modal used on the sign-in page |
| `components/PasswordInput.tsx` | Reusable password input with show/hide toggle and error state |
| `components/icons.tsx` | Shared SVG icon components used across pages |
| `types/article.ts` | Shared `Article` TypeScript interface used across all pages |
| `util/format.ts` | Shared date formatting and text truncation utilities |
| `middleware.ts` | Edge middleware: JWT decode with jose signature verification, protected route redirects |
| `Dockerfile` | Production container configuration |
| `.github/workflows/deploy.yml` | Frontend CI/CD pipeline (auto-deploy to AWS EC2) |
| `README.md` | Frontend setup guide, scripts, key features, folder structure |

---

## Shelly Huang — Backend Article CRUD & Frontend Article UX

### Backend (`IP_Group_Assignment_Backend/`)

| File | Description |
|------|-------------|
| `app/models/article.py` | `Article` Beanie document with title, content, summary, author, and AI job fields |
| `app/routers/article.py` | Article endpoints: create (triggers AI background job), list (public), get by ID (public), update, delete |
| `app/main.py` | Co-authored: registered `Article` document model in Beanie startup |

### Frontend (`IP_Group_Assignment_Frontend/`)

| File | Description |
|------|-------------|
| `app/articles/[id]/page.tsx` | Article detail UX enhancements: table of contents, reading progress bar, reading time estimate, back-to-top button, sticky floating action bar, copy-link button, print feature, AI summary position; co-authored with Dequan and Kai |
| `app/articles/page.tsx` | Article listing enhancements: article count display, recently-viewed section integration; co-authored with Dequan and Kai |
| `app/profile/page.tsx` | Profile page UX improvements; co-authored with Kai |
| `components/RecentlyViewedArticles.tsx` | Standalone recently-viewed articles component (localStorage-based tracking) |
| `components/footer/footer.tsx` | Footer dark mode support |
| `components/footer/footer.sass` | Footer dark mode styles |
| `components/header/header.tsx` | Header dark mode support |
| `hooks/useTheme.ts` | Dark/light mode theme toggle hook |
| `tailwind.config.js` | Dark mode configuration (`darkMode: 'class'`) |
| `styles/main.css` | Dark mode and layout style additions |

---

## Dequan Xu — Frontend Architecture, Admin Panel & Article Pages

### Frontend (`IP_Group_Assignment_Frontend/`)

| File | Description |
|------|-------------|
| `app/layout.tsx` | Root layout: fonts, global styles, header, footer |
| `app/home/page.tsx` | Home page: hero section, featured article, recent articles list, CTA banner |
| `app/articles/page.tsx` | Articles listing page: client-side search, pagination (9 per page); co-authored with Kai and Shelly |
| `app/articles/[id]/page.tsx` | Article detail page: markdown rendering, bookmark toggle; co-authored with Kai and Shelly |
| `app/admin/page.tsx` | Admin dashboard: stats overview and navigation links |
| `app/admin/articles/page.tsx` | Admin article management: create/edit/delete articles with inline form |
| `app/admin/users/page.tsx` | Admin user management: list all users, live search, edit role, delete |
| `app/bff/articles/route.ts` | BFF GET proxy for articles list (nginx-compatible) |
| `app/bff/articles/[id]/route.ts` | BFF GET proxy for single article |
| `app/api/articles/route.ts` | Internal API route for article list |
| `app/api/articles/[id]/route.ts` | Internal API route for single article |
| `app/api/admin/users/route.ts` | Internal API route for admin user management |
| `app/api/admin/stats/route.ts` | Internal API route for admin statistics |
| `actions/articles.ts` | Server actions: `createArticleAction`, `updateArticleAction`, `deleteArticleAction` |
| `actions/admin.ts` | Server actions: admin user list, update role, delete user |
| `actions/user.ts` | Server action: `updateUserAction` (name/email update) |
| `components/header/header.tsx` | Site header: navigation, auth state, mobile menu; co-authored with Shelly |
| `components/header/header.sass` | Header styles; co-authored with Shelly |
| `components/footer/footer.tsx` | Site footer; co-authored with Shelly |
| `components/footer/footer.sass` | Footer styles; co-authored with Shelly |
| `hooks/useAuth.ts` | `useUser` hook — fetches current user, exposes `isAdmin` |
| `hooks/useUser.ts` | `updateUser` helper for profile edits |
| `util/api/backend.ts` | Response normalisation helpers (`normalizeArticleResponse`, etc.) |
| `util/api/backendErrors.ts` | `messageFromApiError` error parser |
| `util/api/client.ts` | `API_BASE` URL constant |
| `util/api/publicArticles.ts` | `fetchPublicArticlesList` and `fetchPublicArticleById` utilities |
| `styles/global.sass` | Global SASS styles and CSS custom properties |
| `styles/main.css` | Compiled Tailwind entry point; co-authored with Shelly |
| `tailwind.config.js` | Tailwind theme: brand colours, typography, custom utilities; co-authored with Shelly |
| `package.json` | Node.js dependencies and scripts |
| `tsconfig.json` | TypeScript compiler configuration |
