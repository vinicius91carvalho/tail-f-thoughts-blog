---
title: "How I Turned My Android Into a Vibe Coding Workstation"
subtitle: "No laptop? No problem. How I set up a Samsung S24 Ultra with Termux, proot Ubuntu, Claude Code, and VS Code — and actually shipped real features from my phone."
slug: android-vibe-coding-workstation
cover: https://raw.githubusercontent.com/vinicius91carvalho/tail-f-thoughts-blog/master/assets/images/android-vibe-coding/dex-desktop-setup.jpg
domain: tail-f-thoughts.hashnode.dev
tags: android, claude-ai, mobile-development, programming
publishedAt: 2026-03-06T10:00:00.000Z
---

I was working with the company notebook, but when I went out I thought: no problem, I'm going to buy a new laptop. I was thinking about a machine that would stay with me for years. But here in Brazil, the machine I wanted is insanely expensive. You already know what I'm talking about — a MacBook Pro. The Brazilian price is brutal.

So I did some research and found decent prices on [GoImports](https://www.goimports.com.br) (no, I'm not getting paid to promote them, unfortunately). They're reliable and the support is great, but I needed to wait 20 working days for my machine to arrive.

I can't wait that long. I need to do something.

Then I remembered — my Android smartphone has a desktop mode. I have a Samsung S24 Ultra with DEX, where I can connect a monitor via USB-C or mirror the screen over Wi-Fi. But I didn't expect to actually *use it* as my daily driver.

This post will teach you how to turn your smartphone into a workstation and code from anywhere — as long as you have a decent internet connection.

## You Need a Good Terminal App

The best terminal app I found was [Termux](https://github.com/termux/termux-app). Simple, reliable, open source. But there are some tricks.

**Download Termux from GitHub, not from the Play Store.** The Play Store version has limited access because of Google's security layer. Here's the link for their releases: [github.com/termux/termux-app/releases](https://github.com/termux/termux-app/releases) — grab the latest stable APK.

This would be enough... until you discover that sometimes your phone gets warm and Android just kills the process when it consumes too much CPU or memory.

### Configure Android to Not Kill Termux Unexpectedly

You need to enable a feature called **"Disable child process restrictions"**. This disables the "Phantom Process Killer" — a feature introduced in Android 12 to keep system resources in check. Great for battery life, nightmare for Termux users. It kills heavy background tasks without warning. This toggle is available on Android 12L and later — if you're on plain Android 12, you'll need ADB commands instead.

Here's how:

1. Enable **Developer Options** on your phone: Settings > About Phone > Tap "Build Number" 7 times
2. Go back to the main Settings menu and open **Developer Options**
3. Find and enable **"Disable child process restrictions"**

### Disable Battery Optimization

Even after fixing the process killer, Android might still put the app to sleep. To prevent this:

1. Long-press the Termux icon > **App Info**
2. Go to **Battery** or **Battery Usage**
3. Select **Unrestricted**

## Opening Termux and Installing Essential Tools

Open the Termux app and let's get it ready.

**1) Update packages:**

```bash
pkg update && pkg upgrade
```

**2) Grant storage access** so Termux can reach your phone's internal storage (Downloads, Photos, etc.):

```bash
termux-setup-storage
```

**3) Install the starter pack.** This is what turns Termux from a simple terminal into a functional Linux workstation. `tmux` lets you split windows however you want, and `proot-distro` allows you to install full distributions like Ubuntu, Debian, or Arch inside Termux.

```bash
pkg install wget curl git unzip tmux proot-distro -y
```

## Installing Linux and Setting Up Your Workflow

**1) Install your Linux distribution.** I went with Ubuntu, but pick whatever you're familiar with:

```bash
proot-distro install ubuntu
```

**2) Enter the Linux environment** and share a folder with Android:

```bash
proot-distro login ubuntu --shared-tmp --bind /storage/downloads:/android_files
```

**3) Update the system:**

```bash
apt update && apt upgrade -y
```

## Installing Your Workspace

I use Claude Code as my primary coding tool, so I'm basically vibe coding in English — which is totally appropriate for a small phone screen. When I need to read code carefully, I share my screen with a monitor or TV and open VS Code.

![Claude Code running on the phone screen — yes, it works](https://raw.githubusercontent.com/vinicius91carvalho/tail-f-thoughts-blog/master/assets/images/android-vibe-coding/terminal-claude-code.jpg)

Here's how to set up the same environment:

**1) Install basic tools:**

```bash
apt update && apt upgrade -y
apt install curl wget git nano unzip build-essential -y
```

**2) Install NVM and Node.js LTS:**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install --lts
nvm use --lts
nvm alias default 'lts/*'
```

**3) Install Code Server** to run VS Code on port 8080 (or any port you define):

```bash
curl -fsSL https://code-server.dev/install.sh | sh
```

**4) Install Claude Code CLI:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

Done. You have a vibe coding workstation on your phone.

![Claude Code welcome screen — Opus 4.6 running inside proot on Android](https://raw.githubusercontent.com/vinicius91carvalho/tail-f-thoughts-blog/master/assets/images/android-vibe-coding/terminal-claude-welcome.jpg)

## Tips

**1)** To run Claude Code bypassing permission prompts (useful inside the sandboxed proot environment):

```bash
IS_SANDBOX=1 claude --dangerously-skip-permissions
```

**2)** Use `tmux` only if you have a big monitor or TV. Termux itself supports multiple terminals — just swipe your finger from the left edge of the screen to the right to switch between them.

**3)** To type text in Termux, there's a bottom bar you can swipe right to reveal the text mode. Tap it and the keyboard appears.

**4)** I bought a small USB fan because the phone gets warm when I have a lot running. Sounds silly, but it makes a real difference.

## Limitations

The first one that got me was **Turbopack**. The new Next.js bundler — the one that promises blazing fast builds — in my setup, it simply didn't work inside the proot container. It crashed with an `invalid symlink` error and I couldn't find a fix. I just fell back to Webpack and moved on.

The next one is subtler. In my case, the **Next.js dev server crashed on startup** when I didn't explicitly set the hostname. I believe it internally tries to call `os.networkInterfaces()` to figure out where to bind, and that system call doesn't behave correctly inside proot. The fix is simple — always pass `--hostname 127.0.0.1` — but it took me a while to understand why it was happening.

Running the **production server** had its own quirk too. It needed to be started from the app's own directory, not from the project root. No error message tells you this clearly. It just fails.

And if you're writing tests with **Playwright**, forget about Chrome. On ARM64 you get Chromium and that's it. The regular Chrome binary isn't available for that architecture, so your test setup needs to account for that from day one.

## Extras: Performance Tuning

### Inside proot (Ubuntu)

Add this to your `~/.bashrc` inside the proot environment:

```bash
# nano ~/.bashrc

# Quick alias for Claude Code with sandbox bypass
alias claude="IS_SANDBOX=1 claude --dangerously-skip-permissions"

# Enable LSP tool for Claude Code
export ENABLE_LSP_TOOL=1

# Raise CPU priority for the current shell
renice -n -15 -p $$ >/dev/null 2>&1
```

### Inside Termux

Create or edit your `~/.bashrc` in Termux (outside proot):

```bash
# touch ~/.bashrc && nano ~/.bashrc

# Prevent Android from suspending the process
termux-wake-lock

# Pin to performance cores on Snapdragon 8 Gen 3 (A720 cluster — core mapping varies by device)
taskset -p -c 4-7 $$ >/dev/null 2>&1
```

## My Current Setup

![The full DEX desktop — VS Code on the left, Claude Code on the right](https://raw.githubusercontent.com/vinicius91carvalho/tail-f-thoughts-blog/master/assets/images/android-vibe-coding/dex-desktop-setup.jpg)

I bought a few peripherals to make this actually comfortable:

- **Keyboard**: Logitech Pebble Keys 2 K380s
- **Mouse**: Logitech M720 Triathlon
- **Monitor**: Dell P3225 QE
- **Cooling**: Mini Fan Basike

Is it a MacBook? No. But honestly, for vibe coding with Claude Code, it gets the job done. I've been shipping real features from this setup while waiting for my laptop to arrive.

---

*Got questions or ran into issues setting this up? Hit me in the comments — I've probably hit the same wall and can help you get past it.*
