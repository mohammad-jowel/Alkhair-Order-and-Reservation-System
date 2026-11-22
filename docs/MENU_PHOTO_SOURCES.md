# Menu Image Provenance

## Current catalog images

The 68 locally stored WebP files in `main/media/menu_items/catalog/` are **AI-enhanced restorations and illustrations** based on crops from the supplied original restaurant-menu artwork. They are not third-party stock photography and may differ from dishes served.

On **November 22, 2026**, the catalog was generated with OpenAI `gpt-image-2-high` using the original menu artwork as the reference source:

- **Yemeni Specialties (12 distinct assets):** conservative AI photo restorations. Their prompts preserve the source crop's dish, serving vessel, portion, camera angle, and lighting while reducing blur and removing the poster background.
- **All other categories (56 distinct assets):** AI-generated menu illustrations based on the same original artwork.

All assets are normalized to 1400 × 900 WebP canvases and retain their existing filenames so the seeded menu paths remain stable. The previous Wikimedia Commons assets were replaced; no third-party stock image is used by the current catalog.

## Customer-facing disclosure

The public menu and homepage say that menu images are AI-enhanced restorations and illustrations based on the restaurant's original menu artwork, and that they may differ from items served.

## Maintenance

- Keep the disclosure whenever these assets are displayed.
- Do not describe them as verified restaurant photography.
- If a specialty image starts to look synthetic or no longer matches the source, regenerate it conservatively from the approved source crop rather than from a text-only prompt.
- Replace all assets with approved restaurant photography when available.
- If a menu item's visual reference changes, regenerate that specific image from the approved source while retaining the filename used by `seed_restaurant_demo`.
