# KiCad tooling choice

The requested [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) was installed locally at `../tools/KiCAD-MCP-Server`, version 2.7.0, commit `ac716d1a8bfad325b4aa93a398222645b3f78fd7`.

Its Node dependencies and TypeScript server were built, and its Python dependencies were installed into a project virtual environment using KiCad's bundled Python 3.9. The MCP server was exercised over local standard input/output and used to create the native project. `../tools/kicad-call.mjs` is the local MCP client wrapper. This is a working local installation, not a globally registered Codex plugin or an exposed network service.

For this design, the most reliable tested workflow was a combination of the MCP server, native KiCad libraries/Python bindings, native command-line validation and GUI inspection. Native KiCad ERC and DRC were the final authority. The server's early-start Python readiness race required a limited retry in the local client. TypeScript compilation was restricted to the server's own type directories to avoid unrelated parent-directory packages.

The repository now points to [Konnect](https://github.com/mixelpixx/Konnect), its newer native-IPC successor with KiCad 10/macOS support. It was researched but not installed. There was no need to replace the working toolchain mid-design. This is a recommendation based on the setup tested here, not a comparative benchmark of every KiCad automation tool. KiCad's API transition is documented in the [official API overview](https://dev-docs.kicad.org/en/apis-and-binding/index.html).

Routing ran locally with [Freerouting](https://github.com/freerouting/freerouting) 2.4.1 and a portable Temurin Java 25 runtime. Analytics and its API server were disabled for routing. No board was uploaded to a cloud autorouter. Both downloaded archives were checked against the release-provider SHA-256 values:

- Freerouting JAR: `251101c3eeac22d7e7dfcf6796603279e5d1000283eb82d8f093780f7afc6aa9`
- Temurin JRE archive: `5b02bcc908da092e7e00b9772d4f9bbb87f44a60b7c90f7cf5a91a1d98f37e1b`

The root `hardware/*.py` files record the generation and routing iterations. The checked native CAD files are the deliverable; these scripts are not a supported one-click regeneration pipeline and may overwrite manual work. Use KiCad for subsequent edits and rerun ERC/DRC and manufacturing exports afterward. The local MCP installation is not required merely to open or edit the project.
