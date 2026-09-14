import { WORKPLACE_SCENARIO_SLUG } from "../data/workplaceStories.js";

export { WORKPLACE_SCENARIO_SLUG };

export function workplaceStartView(serviceModeId) {
  return serviceModeId === "workplace" ? "preview" : "role";
}

export function isWorkplaceSession(session) {
  return session?.interaction?.mode === "workplace" || session?.scenario?.slug === WORKPLACE_SCENARIO_SLUG;
}

export function workplaceBriefing(interaction) {
  if (interaction?.mode !== "workplace") return null;
  return interaction.briefing || null;
}
