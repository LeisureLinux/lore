# NEWS for rsync 3.5.0

**Release date:** 13 August 2026

## Overview

The rsync development team is proud to announce the 3.5.0 release after several months of focused work. This release addresses a significant number of security issues, improves robustness, and adds several new features.

## Security fixes

This release fixes **33 security issues** discovered during a focused audit of rsync's path handling and daemon protocol, complemented by a companion daemon-protocol fuzzing pass and reports from external researchers. Every fix ships with a regression test that fails on the unfixed tree. CVE identifiers were assigned by VulnCheck (CNA), with many advisories narrower than "everything before 3.5.0".

Key security highlights include:

- **Link following (CWE-59/61):** A local user who controls a path component can plant a symlink that a privileged rsync then follows. This can lead to arbitrary file read or transfer-shaping via symlinked operator-supplied input files. (CVE-2026-53802 HIGH)

- **Filter merge symlink attacks:** rsync followed attacker-planted symlinks in `--filter` merge files, including per-directory merges and `-C` `.cvsignore`.

- **Daemon protocol hardening:** Several protocol-level vulnerabilities have been patched, and numerous robustness hardenings applied throughout the codebase.

## Acknowledgments

Special thanks to Zen Dodd (Tao), Omar Elsayed (seks99x), Will Sargeant, Paul Mackerras, Aleksa Sarai, and Leonid Bugaev (buger) for joining the rsync admins group to help triage issues, develop new tests, review PRs, and develop guidelines for distinguishing security issues from expected behaviour. Additional gratitude to Filipe Casal from Trail of Bits for the "Patch the Planet" program, and to Greg Kroah-Hartman and Stuart Inglis for security reports and testing.

## Getting rsync 3.5.0

Visit the official source: https://download.samba.org/pub/rsync/

