# Contributing to Helios Memory Substrate

Thank you for your interest in contributing to Helios Memory Substrate. This project welcomes contributions from developers, researchers, and engineers.

## License

This project is licensed under the **PolyForm Noncommercial License 1.0.0 with Commons Clause**. See the [LICENSE](LICENSE) file for full terms.

## Contributor License Agreement (Inbound = Outbound)

By submitting a contribution (pull request, patch, issue, or any other form of contribution) to this project, you agree that:

1. **Your contribution is licensed to the project owner (Thomas Papenbrock) under the same license that governs this project** — the PolyForm Noncommercial License 1.0.0 with Commons Clause. This is the "inbound = outbound" principle: the license you receive to use this project is the same license under which you contribute back.
2. You have the right to submit your contribution under these terms (i.e., you own the code or have permission to contribute it).
3. You grant the project owner a perpetual, worldwide, non-exclusive, royalty-free license to use, reproduce, modify, and distribute your contribution as part of the project.

## Developer Certificate of Origin (DCO)

All contributors must sign off on their commits using the **Developer Certificate of Origin (DCO)**. By adding a `Signed-off-by` line to your commit message, you certify that you wrote the contribution or otherwise have the right to submit it under the project license.

To sign off on a commit, add the following line at the end of your commit message:

```
Signed-off-by: Your Name <your.email@example.com>
```

You can do this automatically with:

```
git commit -s -m "Your commit message"
```

The full text of the DCO is available at https://developercertificate.org/.

**Pull requests that do not include a DCO sign-off on all commits will not be merged.**

## How to Contribute

1. Fork the repository.
2. Create a feature branch:
   ```
   git checkout -b feature/my-feature
   ```
3. Commit your changes with clear messages and a DCO sign-off:
   ```
   git commit -s -m "feat: describe your change"
   ```
4. Push your branch:
   ```
   git push origin feature/my-feature
   ```
5. Open a Pull Request using the provided template.

## Testing Requirements

- Include unit tests for new features.
- Ensure existing tests pass.
- Document any new configuration or environment variables.

## Branching Model

- main — stable, production-ready
- dev — active development
- feature/* — new features
- fix/* — bug fixes

## Code Style

- Follow PEP8.
- Use descriptive variable names.
- Document complex logic.
- Keep functions small and modular.

## Pull Request Requirements

- Clear description of changes.
- Screenshots or logs if applicable.
- Tests included.
- No breaking changes without discussion.
- DCO sign-off on all commits.

Thank you for helping build Helios Memory Substrate.
