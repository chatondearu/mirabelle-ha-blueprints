import type { NodeTypesObject } from '@vue-flow/core'
import ActionNode from './ActionNode.vue'
import BlueprintInputNode from './BlueprintInputNode.vue'
import BlueprintMetaNode from './BlueprintMetaNode.vue'
import ChooseNode from './ChooseNode.vue'
import ChooseOptionNode from './ChooseOptionNode.vue'
import ConditionNode from './ConditionNode.vue'
import DelayNode from './DelayNode.vue'
import HaBlockNode from './HaBlockNode.vue'
import InputsNode from './InputsNode.vue'
import InputsVariablesNode from './InputsVariablesNode.vue'
import ParallelNode from './ParallelNode.vue'
import RepeatNode from './RepeatNode.vue'
import RootNode from './RootNode.vue'
import SequenceNode from './SequenceNode.vue'
import StandardNode from './StandardNode.vue'
import TriggerNode from './TriggerNode.vue'
import VariableNode from './VariableNode.vue'
import VariablesNode from './VariablesNode.vue'
import WaitNode from './WaitNode.vue'

/**
 * Central registry for node renderers.
 * New HA block node kinds should be wired here.
 */
export const FLOW_NODE_RENDERER_MAP: NodeTypesObject = {
  action: ActionNode,
  blueprint_input: BlueprintInputNode,
  blueprint_meta: BlueprintMetaNode,
  choose: ChooseNode,
  choose_option: ChooseOptionNode,
  condition: ConditionNode,
  delay: DelayNode,
  ha_block: HaBlockNode,
  inputs: InputsNode,
  inputs_variables: InputsVariablesNode,
  parallel: ParallelNode,
  repeat: RepeatNode,
  root: RootNode,
  sequence: SequenceNode,
  trigger: TriggerNode,
  variable: VariableNode,
  variables: VariablesNode,
  wait: WaitNode,
  flow: StandardNode,
}

