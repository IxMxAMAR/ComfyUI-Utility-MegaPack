export default {
  id: "nord",
  displayName: "Nord",
  motion: "none",
  staticConfig: {
    bgcolor: "#2e3440",
    color: "#3b4252",
    titlecolor: "#3b4252",
    titletext: "#eceff4",
    boxcolor: "#88c0d0",
  },
  wirePalette: {
    default: "#88c0d0",   // frost
    IMAGE: "#a3be8c",     // aurora green
    LATENT: "#b48ead",    // aurora purple
    MASK: "#eceff4",      // snow
    CONDITIONING: "#ebcb8b", // aurora yellow
    MODEL: "#bf616a",     // aurora red
    CLIP: "#d08770",      // aurora orange
  },
  categoryAccents: {
    image: "#a3be8c",
    latent: "#b48ead",
    conditioning: "#ebcb8b",
    sampling: "#88c0d0",
    loaders: "#d08770",
    default: "#88c0d0",
  },
  groupColors: { color: "#88c0d0", bgcolor: "#3b4252" },
  bgGridColor: "#242933",
  themeApiVersion: 2,
};
