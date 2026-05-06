export class ThemeRegistry {
  #map = new Map();

  register(theme) {
    if (!theme || !theme.id) {
      throw new Error("theme is missing 'id'");
    }
    if (this.#map.has(theme.id)) {
      throw new Error(`duplicate theme id: ${theme.id}`);
    }
    this.#map.set(theme.id, theme);
  }

  get(id) { return this.#map.get(id); }
  has(id) { return this.#map.has(id); }
  ids() { return [...this.#map.keys()].sort(); }
  get size() { return this.#map.size; }
}
