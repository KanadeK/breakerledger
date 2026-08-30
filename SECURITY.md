# Security policy

## Supported version

The latest tagged release receives security fixes.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not place
sensitive sample data, credentials, or an exploit payload in a public issue.

Include the affected version, input shape, observed result, expected result,
and the smallest safe reproduction you can provide.

## Scope

Security-relevant behavior includes:

- CSV or HTML injection;
- writing outside the requested five output filenames or following report symlinks;
- unbounded input processing;
- runtime network, shell, or dynamic-code execution;
- hidden contradictions or evidence loss that can make a mapping appear stronger;
- secrets included in source, fixtures, packages, or logs.

BreakerLedger is documentation software, not electrical-safety or
code-compliance software. A wrong observation can produce a wrong result; source
observation IDs and counts remain visible so mappings can be reviewed.
