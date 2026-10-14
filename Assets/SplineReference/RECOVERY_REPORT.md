# Public Spline reference: recovered evidence

Source: https://app.spline.design/file/4d17acdc-e288-41f6-953d-584bf74d5b5d

Title verified in browser and public metadata: **Modern Industrial Art Gallery**. Retrieval: 2026-10-13 UTC. Anonymous permissions: **view**, not edit. No Spline content was changed; no login, credentials, or verification challenge were used.

## Use these images

- `recovery_diagnostic.png`: actual loaded current editor Preview tab, captured directly from the requested file. The lower portion is black and some elements appear displaced from this camera. This is what the source actually displayed, not a reconstruction.
- `Reference_Server_Preview.jpg`: original image naturally disclosed by the public file metadata, https://filespreview.spline.design/4d17acdc-e288-41f6-953d-584bf74d5b5d.jpg . It corroborates the same low/clipped-looking current-editor composition. Its exact render time is unknown.
- `Published_Reference_Preview.png`: clean runtime render from the file's **published export**, https://my.spline.design/modernindustrialartgallery-aabLwPd48O0FUQHYCbiwQ5D7/ . This provides a usable floor-level/layout view but is NOT guaranteed to equal the latest editor revision.

**Do not use** `Spline_Editor.png` (pre-existing) or `FAILED_Loading_Attempt.png` as gallery evidence: both are blank loading captures. The first recovered editor capture genuinely rendered; a second editor attempt remained loading. These intermittent results do not establish a root cause. Enabling Chrome's unsafe SwiftShader fallback coincided with the successful attempt, but does not prove the earlier failures were GPU-related.

## Visible architecture, without guessed dimensions

The current editor/server-preview images visibly show:
- A dark exposed ceiling with closely spaced parallel members and open-web steel-like trusses.
- Light-colored track rails carrying many cylindrical spot fixtures, plus a broad curved/oval overhead rail.
- A bright metallic cylindrical duct crossing beneath the ceiling.
- Plain light walls with brightly colored rectangular framed abstract paintings and small dark caption plaques.
- A tall curved white freestanding partition near the middle of the view, carrying a small circular dark marker.
- A large gold/brown intertwined-band sculpture on a dark rectangular plinth to the right; a smaller silver sphere/brown curved sculpture toward the left rear.

The published runtime screenshot additionally clearly shows a dark reflective floor, a white floor-guide line, and a low wood-slat bench with a pale cushion in the foreground. Do not treat the current-editor black foreground or apparently floating bench as established intended architecture. No stairs, mezzanine, room dimensions, or walkability claims are established by these captures.

## Recovered source and metadata

Discovery endpoint (observed in normal browser network traffic, then read anonymously):
`https://apis.spline.design/file/signed/4d17acdc-e288-41f6-953d-584bf74d5b5d`

- `public_scene_metadata.json`: title, file UUID, access=view, preview/export URLs and update timestamp. Signed query parameters omitted.
- `Published_Reference.splinecode`: **313046 bytes**, extracted exactly from the published page's inline `app.start([...])` byte array, not invented or reconstructed. SHA-256: `e95e98daca4e7e00626cdcdeb957c4e0edcfea41e2dbf954fd8461e337516059`.
- `Reference_Export_Decoded.html`: original public export HTML after Brotli decompression. `Reference_Export.http-body.br` preserves its compressed HTTP body.
- `published_scene_data.json`: complete public runtime `app.data` readback (schema, scene, frames, shared, version).
- `published_runtime_metadata.json`: all 397 entries returned by public `getAllObjects()`, with names, types and transforms. 386 meshes, 5 point lights, 5 spot lights, 1 directional light. There are 394 distinct names; the four `Bench Leg` objects must not be deduplicated. Runtime IDs returned null.
- `published_object_inventory.json`: programmatically counted inventory and all names.
- `published_camera_metadata.json`: original published camera data and its location in the source tree. The published personal camera is PerspectiveCamera, FOV=45, position `[-332.0649666224441,209.17310096006543,651.1436965987891]`, rotation `[-9.854960903761514,-35.595912840025434,-5.773848417359876]`, up `[0,1,0]`, near=70, far=100000. Preserve raw Spline values; physical unit scale and rotation convention were not independently validated. The runtime object rotations use radians, while these raw camera rotation values must not be assumed to use the same convention.
- `verified_evidence_manifest.json`: byte counts and hashes for the principal evidence files.

The published page loaded using Spline runtime 2.0.76, rendered successfully, and yielded no page errors. For metadata readback only, a local interception added `window.__referenceApp=app` to expose the existing Application variable. This did not change scene data, camera pose, materials, or server content.

## Revision limitation / what the user must supply

The public file metadata's updateDate is **2026-10-13T23:11:03Z**. The published export HTTP Last-Modified was **2026-10-12 20:12:46 GMT**, so the exported source is an earlier published snapshot. It is useful and explicitly associated with the requested file, but must not be labeled the exact latest editor source.

The metadata-disclosed signed native ZIP URL returned **HTTP 404**, not a login or verification denial. No guessed alternate storage paths were attempted. To obtain the exact latest editable source, the user should supply a fresh **native `.spline` export of this file**, or republish this exact file and supply its updated public export. They need not send a password or verification code.

Project changes are limited to this evidence folder; recovery scripts are in Hermes scratch. The reusable public-reference recovery procedure was also recorded in the existing Spline skill. No Unreal source, scripts, maps, or project configuration were touched; Unreal was not launched.
