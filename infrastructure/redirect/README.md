# Domain redirect

The Vercel project `yautja-redirect` forwards `www.yautja.ai` and all its paths to `https://github.com/petehottelet/yautja` with an HTTP 308 redirect.

Deploy only this directory. It contains the redirect configuration and a fallback link; the converter, model cache, source media, and skill archive are not deployment inputs.

```bash
cd infrastructure/redirect
vercel link --project yautja-redirect --scope petehottelets-projects --yes
vercel deploy --prod --scope petehottelets-projects --yes
```

The domain must point to the DNS target shown in the Vercel project's Domains settings. Validate the live `Location` response header after DNS changes. This project is deployed independently of GitHub releases.
