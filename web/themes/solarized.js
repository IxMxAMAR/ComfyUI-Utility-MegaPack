export default {
  id: "solarized_dark",
  displayName: "Solarized Dark",
  motion: "none",
  staticConfig: {
    bgcolor: "#002b36",
    color: "#073642",
    titlecolor: "#073642",
    titletext: "#b58900",
    boxcolor: "#b58900",
  },
  wirePalette: {
    default: "#b58900",   // yellow
    IMAGE: "#268bd2",     // blue
    LATENT: "#6c71c4",    // violet
    MASK: "#93a1a1",      // base1
    CONDITIONING: "#d33682", // magenta
    MODEL: "#dc322f",     // red
    CLIP: "#cb4b16",      // orange
  },
  categoryAccents: {
    image: "#268bd2",
    latent: "#6c71c4",
    conditioning: "#d33682",
    sampling: "#859900",
    loaders: "#cb4b16",
    default: "#b58900",
  },
  groupColors: { color: "#b58900", bgcolor: "#073642" },
  bgGridColor: "#002129",
  themeApiVersion: 1,
};
