# WSL development stability

Observed WSL capacity was 3.8 GiB RAM, 1 GiB swap, and four CPUs. Scope Guard's four running
containers used about 110 MiB combined; the VS Code extension host was the largest observed
process at about 850 MiB. No kernel OOM kill was recorded. Docker CLI failures coincided with
Docker Desktop stopping, so they are not attributed solely to project memory usage.

Repository mitigations serialize pnpm work in `.npmrc`, limit Compose build parallelism in the
Makefile, run Playwright with one worker, and stop the demo when it is not needed. Build, browser,
and Docker image-pull phases should be run sequentially on a 4 GiB WSL allocation.

For more headroom, the developer can place the following in Windows `%UserProfile%\.wslconfig`
and then run `wsl --shutdown` from PowerShell. This was **not** applied automatically:

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB

[experimental]
autoMemoryReclaim=gradual
```

Choose values appropriate to physical RAM. Keep Docker Desktop WSL integration enabled, verify
`docker info` and `docker run --rm hello-world` after restart, and avoid running a Next.js build,
browser download, and multi-image Compose build concurrently.
