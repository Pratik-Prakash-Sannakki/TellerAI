// Agent hand-back: a toolbar button and a badge. No content scripts, no host access.
// The notebook reads `self.handbackClicked` and calls `setMode` over the service worker.
self.handbackClicked = 0;

const MODES = {
  YOU: { color: "#2e7d32", title: "You are in control: click to hand back to the agent" },
  AI: { color: "#616161", title: "Agent hand-back: the agent is in control" },
};

self.setMode = (who) => {
  const mode = MODES[who] || MODES.AI;
  chrome.action.setBadgeText({ text: who in MODES ? who : "AI" });
  chrome.action.setBadgeBackgroundColor({ color: mode.color });
  chrome.action.setTitle({ title: mode.title });
};

chrome.action.onClicked.addListener(() => {
  self.handbackClicked = (self.handbackClicked || 0) + 1;
  chrome.action.setBadgeText({ text: "OK" });
});

self.setMode("AI");
