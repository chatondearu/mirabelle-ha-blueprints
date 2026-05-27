import type { NodeTypesObject } from '@vue-flow/core'
import ActionNode from './ActionNode.vue'
import BlueprintGroupNode from './BlueprintGroupNode.vue'
import BlueprintInputNode from './BlueprintInputNode.vue'
import ChooseNode from './ChooseNode.vue'
import ChooseOptionNode from './ChooseOptionNode.vue'
import ConditionNode from './ConditionNode.vue'
import DelayNode from './DelayNode.vue'
import HaBlockNode from './HaBlockNode.vue'
import IfContainerNode from './IfContainerNode.vue'
import ParallelNode from './ParallelNode.vue'
import RepeatNode from './RepeatNode.vue'
import SequenceNode from './SequenceNode.vue'
import StandardNode from './StandardNode.vue'
import TriggerNode from './TriggerNode.vue'
import VariableNode from './VariableNode.vue'
import VariablesGroupNode from './VariablesGroupNode.vue'
import WaitNode from './WaitNode.vue'

/**
 * Central registry for node renderers.
 * New HA block node kinds should be wired here.
 */
export const FLOW_NODE_RENDERER_MAP: NodeTypesObject = {
  action: ActionNode,
  blueprint: BlueprintGroupNode,
  blueprint_input: BlueprintInputNode,
  choose: ChooseNode,
  choose_option: ChooseOptionNode,
  condition: ConditionNode,
  delay: DelayNode,
  if: IfContainerNode,
  ha_block: HaBlockNode,
  parallel: ParallelNode,
  repeat: RepeatNode,
  sequence: SequenceNode,
  trigger: TriggerNode,
  variable: VariableNode,
  variables: VariablesGroupNode,
  wait: WaitNode,
  flow: StandardNode,
}
