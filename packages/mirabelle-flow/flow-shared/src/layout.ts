/** Default graph layout spacing (pixels). */
export const FLOW_LAYOUT = {
  startX: 80,
  startY: 80,
  horizontalGap: 488,
  verticalGap: 100,
  /** Minimum vertical offset between config band and execution flow (px). */
  configBandMinHeight: 220,
  /** Gap below the tallest config group before execution nodes (px). */
  configExecGap: 48,
  configGroupWidth: 240,
} as const

/** Shared sizing/gutter constants used by core and UI. */
export const FLOW_NODE_METRICS = {
  cardWidth: 256,
  cardMinWidth: 160,
  cardChildMaxWidth: 224,
  cardSingleLineHeight: 56,
  parentHeaderHeight: 56,
  parentPadding: 18,
  parentChildGap: 14,
  parentHandleClearance: 10,
  parentDepthLimit: 3,
  executionLaneGap: 16,
} as const
