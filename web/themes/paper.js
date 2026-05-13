export default {
  id: "paper_ink",
  displayName: "Paper / Ink",
  motion: "none",
  staticConfig: {
    bgcolor: "#f4ecd8",
    color: "#ede1c2",
    titlecolor: "#ede1c2",
    titletext: "#2a1a0a",
    boxcolor: "#8b1a1a",
  },
  wirePalette: {
    default: "#8b1a1a",
    IMAGE: "#5a3a1a",     // sepia
    LATENT: "#806040",
    MASK: "#2a1a0a",
    CONDITIONING: "#a85a1a",
  },
  categoryAccents: {
    image: "#5a3a1a",
    latent: "#806040",
    conditioning: "#a85a1a",
    default: "#8b1a1a",
  },
  groupColors: { color: "#8b1a1a", bgcolor: "#ede1c2" },
  bgGridColor: "#e8dcbe",
  themeApiVersion: 1,
};
