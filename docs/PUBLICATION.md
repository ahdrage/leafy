# Public publication scope

The public repository starts with a reviewed snapshot of the current project. It does not publish the private working repository's Git history, because that history includes supplier/account records. The original working files and history are retained locally.

Included: current and earlier technical designs, native KiCad source and local libraries, BOMs, manufacturing artwork, scripts, firmware/tests, Blender/STL enclosure source, review images, revision history and engineering reports. G.5 is the current manufacturing revision; historical designs are not alternatives approved for a new order.

Excluded: correspondence, account/order identifiers, delivery/contact details, original supplier spreadsheets, browser screenshots/state, configured secrets/binaries, downloaded toolchains, cached vendor PDFs/web pages and unrelated projects. Source links, useful technical quantities and non-identifying cost summaries remain available.

Public archives may be repackaged to omit private records and preserve licence notices. Public manifests describe the published bytes; they must not be confused with the hashes of private historical handoff packages. The current native PCB/schematic, Gerbers/drills, factory BOM/CPL and printable meshes are preserved byte-for-byte. The standalone G.5 Gerber upload ZIP retains its original bytes. Publication changes do not revise electrical or mechanical design.

Historical baseline archives retain the technical inputs needed for comparisons, with private entries removed and archive membership manifests refreshed. Old reports preserve their original provenance; a quoted historical archive hash is not a claim about a newly repackaged public archive. For manufacturing, use the current G.5 upload files and inspect the new supplier review.

The public source includes empty configuration templates only. Keep local settings, credentials and configured firmware outputs private in future contributions too.

The 16 November update includes the local API source, OpenAPI specification, native SwiftUI app, Xcode project, isolated simulator fixture, tests and empty configuration templates. Exclude `server/.env.local`, all other populated environment files, `server/data/` (command records and process lock), Xcode user state and compiled apps. Simulator screenshots use fake readings and a public test token; no vehicle connection was used for those tests.

Dated verification records describe the state at the time of each test. A historical `pushed: false` or “not flashed” entry is not a statement about later publication or installation. See the dated publication verification report for the exported snapshot; the engineering records retain their original provenance.
