# Future improvements

Yautja supports four segmented looks, still images, configurable color/HUD themes, source-scene grading, Cyber glyphs, silhouette code overlays, and independent display textures. Further work should improve consistency and usability without changing those defaults accidentally.

- **Measure tracking stability.** Evaluate crossings, occlusion, entries/exits and true cuts with annotated clips, lost-mask and ID-switch metrics. Compare the current optical-flow tracker with SAM video memory only when bounded memory and measured improvements justify it. Exposure changes can still reset tracking.
- **Cache segmentation for visual iteration.** Reuse masks and pose for palette/HUD experiments, keyed by source content, preprocessing, model revisions and inference settings, with explicit invalidation and storage limits.
- **Guide setup and preview selection.** Help users choose an environment, thermal look and palette from a short representative preview. Keep expensive inference and explicit model downloads visible, and carry selected settings into the full render.
- **Broaden quality evaluation.** Use varied, permissioned footage and annotated material/subject cases alongside cached-model smoke tests. Distant hands, carried objects, overlapping people and uncertain clothing regions remain difficult; the surface-aware modes reduce some errors but do not recover real temperatures or depth.
