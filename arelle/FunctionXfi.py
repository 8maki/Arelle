'''
Created on Dec 20, 2010

@author: Mark V Systems Limited
(c) Copyright 2010 Mark V Systems Limited, All rights reserved.
'''
import xml.dom
from arelle import (ModelObject, XPathContext, XbrlConst, XbrlUtil, XmlUtil)
from arelle.ModelValue import (qname, QName, dateTime, DATE, DATETIME, DATEUNION, anyURI)
from arelle.FunctionUtil import (anytypeArg, stringArg, numericArg, qnameArg, nodeArg)
from math import (isnan,isinf)

class xfiFunctionNotAvailable(Exception):
    def __init__(self):
        self.args =  (_("xfi function not available"),)
    def __repr__(self):
        return self.args[0]
    
def call(xc, p, localname, args):
    try:
        if localname not in xfiFunctions: raise xfiFunctionNotAvailable
        return xfiFunctions[localname](xc, p, args)
    except xfiFunctionNotAvailable:
        raise XPathContext.FunctionNotAvailable("xfi:{0}".format(localname))

def item(xc, args, i=0):
    if len(args[i]) != 1: raise XPathContext.FunctionArgType(i+1,"xbrl:item")
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:item")
    modelItem = xc.modelItem(args[i][0])
    if modelItem: 
        return modelItem
    raise XPathContext.FunctionArgType(i+1,"xbrl:item")

def item_context(xc, args, i=0):
    return item(xc, args, i).context

def item_context_element(xc, args, name):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    context = item_context(xc, args)
    if context:
        return XmlUtil.descendant(context.element, XbrlConst.xbrli, name)
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def context(xc, p, args):
    return item_context(xc, args)

def unit(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:item")
    modelItem = xc.modelItem(args[0][0])
    if modelItem: 
        modelConcept = modelItem.concept
        if modelConcept.isNumeric and not modelConcept.isFraction:
            return modelItem.unit
        return []
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def unit_numerator(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:unit")
    unit = args[0][0]
    if isinstance(unit,ModelObject.ModelObject): unit = unit.element
    if isinstance(unit,xml.dom.Node) and unit.nodeType == 1 and \
       unit.localName == "unit" and unit.namespaceURI == XbrlConst.xbrli: 
        measuresParent = XmlUtil.descendant(unit, XbrlConst.xbrli, "unitNumerator")
        if measuresParent is None: measuresParent = unit
        return XmlUtil.descendants(measuresParent, XbrlConst.xbrli, "measure")
    raise XPathContext.FunctionArgType(1,"xbrl:unit")
        
def unit_denominator(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:unit")
    unit = args[0][0]
    if isinstance(unit,ModelObject.ModelObject): unit = unit.element
    if isinstance(unit,xml.dom.Node) and unit.nodeType == 1 and \
       unit.localName == "unit" and unit.namespaceURI == XbrlConst.xbrli: 
        measuresParent = XmlUtil.descendant(unit, XbrlConst.xbrli, "unitDenominator")
        if measuresParent is None: return []
        return XmlUtil.descendants(measuresParent, XbrlConst.xbrli, "measure")
    raise XPathContext.FunctionArgType(1,"xbrl:unit")

def measure_name(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:measure")
    unit = args[0][0]
    if isinstance(unit,xml.dom.Node) and unit.nodeType == 1 and \
       unit.localName == "measure" and unit.namespaceURI == XbrlConst.xbrli:
        return qname(unit, XmlUtil.text(unit)) 
    raise XPathContext.FunctionArgType(1,"xbrl:unit")

def period(xc, p, args):
    return item_context_element(xc, args, "period")

def context_period(xc, p, args):
    return parent_child(args, "context", "period")

def parent_child(args, parentName, descendantName):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:" + parentName)
    parent = args[0][0]
    if isinstance(parent,ModelObject.ModelObject): parent = parent.element 
    if isinstance(parent,xml.dom.Node) and parent.nodeType == 1 and \
       parent.localName == parentName and parent.namespaceURI == XbrlConst.xbrli:
        if descendantName.startswith('@'):
            return parent.getAttribute(descendantName[1:])
        elif descendantName == 'text()':
            return XmlUtil.text(parent)
        elif descendantName == 'strip-text()':
            return XmlUtil.text(parent).strip()
        else:
            return XmlUtil.child(parent, XbrlConst.xbrli, descendantName)
    raise XPathContext.FunctionArgType(1,"xbrl:" + parentName)

def is_start_end_period(xc, p, args):
    return is_period_type(args, "startDate")

def is_forever_period(xc, p, args):
    return is_period_type(args, "forever")

def is_duration_period(xc, p, args):
    return is_period_type(args, ("forever","startDate") )

def is_instant_period(xc, p, args):
    return is_period_type(args, "instant")

def is_period_type(args, periodElement):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:period")
    period = args[0][0]
    if isinstance(period,xml.dom.Node) and period.nodeType == 1 and \
       period.localName == "period" and period.namespaceURI == XbrlConst.xbrli:
        return XmlUtil.hasChild(period, XbrlConst.xbrli, periodElement)
    raise XPathContext.FunctionArgType(1,"xbrl:period")

def period_start(xc, p, args):
    return period_datetime(p, args, ("startDate","instant"), False)

def period_end(xc, p, args):
    return period_datetime(p, args, ("endDate","instant"), True)

def period_instant(xc, p, args):
    return period_datetime(p, args, "instant", True)

def period_datetime(p, args, periodElement, addOneDay):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:period")
    period = args[0][0]
    if (isinstance(period,xml.dom.Node) and period.nodeType == 1 and 
        period.localName == "period" and period.namespaceURI == XbrlConst.xbrli):
        child = XmlUtil.child(period, XbrlConst.xbrli, periodElement)
        if child:
            return dateTime( child, addOneDay=addOneDay, type=DATETIME)
        elif periodElement == "instant":
            raise XPathContext.XPathException(p, 'xfie:PeriodIsNotInstant', _('Period is not instant'))
        else:
            raise XPathContext.XPathException(p, 'xfie:PeriodIsForever', _('Period is forever'))
    raise XPathContext.FunctionArgType(1,"xbrl:period")

def entity(xc, p, args):
    return item_context_element(xc, args, "entity")

def context_entity(xc, p, args):
    return parent_child(args, "context", "entity")

def identifier(xc, p, args):
    return item_context_element(xc, args, "identifier")

def context_identifier(xc, p, args):
    return parent_child(args, "context", "identifier")

def entity_identifier(xc, p, args):
    return parent_child(args, "entity", "identifier")

def identifier_value(xc, p, args):
    return parent_child(args, "identifier", "strip-text()")

def identifier_scheme(xc, p, args):
    return parent_child(args, "identifier", "@scheme")

def fact_identifier_value(xc, p, args):
    return XmlUtil.text(item_context_element(xc, args, "identifier")).strip()

def fact_identifier_scheme(xc, p, args):
    return item_context_element(xc, args, "identifier").getAttribute("scheme")

def segment(xc, p, args):
    return item_context_element(xc, args, "segment")

def entity_segment(xc, p, args):
    return parent_child(args, "entity", "segment")

def context_segment(xc, p, args):
    return parent_child(args, "context", "segment")

def scenario(xc, p, args):
    return item_context_element(xc, args, "scenario")

def context_scenario(xc, p, args):
    return parent_child(args, "context", "scenario")

def precision(xc, p, args):
    return infer_precision_decimals(xc, p, args, "precision")

def decimals(xc, p, args):
    return infer_precision_decimals(xc, p, args, "decimals")

def infer_precision_decimals(xc, p, args, attrName):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    if len(args[0]) != 1: raise XPathContext.FunctionArgType(1,"xbrl:item")
    modelItem = xc.modelItem(args[0][0])
    if modelItem: 
        modelConcept = modelItem.concept
        if modelConcept.isNumeric:
            if modelConcept.isFraction: return 'INF'
            from arelle.ValidateXbrlCalcs import (inferredDecimals,inferredPrecision)
            p = inferredPrecision(modelItem) if attrName == "precision" else inferredDecimals(modelItem)
            if isinf(p):
                return 'INF'
            if isnan(p):
                raise XPathContext.XPathException(p, 'xfie:ItemIsNotNumeric', _('Argument 1 {0} is not inferrable.').format(attrName))
            return p
    raise XPathContext.XPathException(p, 'xfie:ItemIsNotNumeric', _('Argument 1 is not reported with {0}.').format(attrName))

def numeric(xc, p, args):
    return conceptProperty(xc, p, args, "numeric")

def non_numeric(xc, p, args):
    return conceptProperty(xc, p, args, "non-numeric")

def fraction(xc, p, args):
    return conceptProperty(xc, p, args, "fraction")

def conceptProperty(xc, p, args, property):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    qn = qnameArg(xc, p, args, 0, 'QName', emptyFallback=None)
    if qn:
        modelConcept = xc.modelXbrl.qnameConcepts.get(qn)
        if modelConcept:
            if property == "numeric": return modelConcept.isNumeric
            if property == "non-numeric": return not modelConcept.isNumeric
            if property == "fraction": return modelConcept.isFraction
    return False

def uncovered_aspect(xc, p, args):
    from arelle.ModelFormulaObject import aspectFromToken, Aspect
    from arelle.FormulaEvaluator import uncoveredAspectValue
    if len(args) not in (1,2): raise XPathContext.FunctionNumArgs()
    aspect = aspectFromToken.get(stringArg(xc, args, 0, "xs:token").strip())
    if aspect == Aspect.DIMENSIONS:
        qn = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
        
    # check function use after checking argument types
    if xc.progHeader and xc.progHeader.element:
        if xc.progHeader.element.localName not in ("formula", "consistencyAssertion", "valueAssertion", "message"):
            raise XPathContext.XPathException(p, 'xffe:invalidFunctionUse', _('Function xff:uncovered-aspect cannot be used on an XPath expression associated with a {0}').format(xc.progHeader.element.localName))
        if xc.variableSet and xc.variableSet.implicitFiltering  == "false":
            raise XPathContext.XPathException(p, 'xffe:invalidFunctionUse', _('Function xff:uncovered-aspect cannot be used with implicitFiltering=false'))
        
    if aspect == Aspect.DIMENSIONS:
        if qn:
            modelConcept = xc.modelXbrl.qnameConcepts.get(qn)
            if modelConcept and modelConcept.isDimensionItem:
                aspect = qn
            else:
                return ()   # not a dimension
            dimValue = uncoveredAspectValue(xc, aspect)
            if isinstance(dimValue, ModelObject.ModelDimensionValue):
                if dimValue.isExplicit: 
                    return dimValue.memberQname
                elif dimValue.isTyped:
                    return dimValue.typedMember
            elif isinstance(dimValue, QName): # qname for explicit or node for typed
                return dimValue
            return ()
    aspectValue = uncoveredAspectValue(xc, aspect)
    if aspectValue is None:
        return ()
    return aspectValue

def identical_nodes(xc, p, args):
    raise xfiFunctionNotAvailable()

def s_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def u_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def v_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def c_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def identical_node_set(xc, p, args):
    raise xfiFunctionNotAvailable()

def s_equal_set(xc, p, args):
    raise xfiFunctionNotAvailable()

def v_equal_set(xc, p, args):
    raise xfiFunctionNotAvailable()

def c_equal_set(xc, p, args):
    raise xfiFunctionNotAvailable()

def u_equal_set(xc, p, args):
    raise xfiFunctionNotAvailable()

def x_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def duplicate_item(xc, p, args):
    raise xfiFunctionNotAvailable()

def duplicate_tuple(xc, p, args):
    raise xfiFunctionNotAvailable()

def p_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def cu_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def pc_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def pcu_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def start_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def end_equal(xc, p, args):
    raise xfiFunctionNotAvailable()

def nodes_correspond(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    node1 = nodeArg(xc, args, 0, "node()?", missingArgFallback=(), emptyFallback=())
    node2 = nodeArg(xc, args, 1, "node()?", missingArgFallback=(), emptyFallback=())
    if node1 == ():
        if node2 == (): return True
        return False
    if node2 == (): return False
    return XbrlUtil.nodesCorrespond(xc.modelXbrl, node1, node2, xc.modelXbrl)

def instance(xc, p, args, i=0):
    if len(args[i]) != 1: raise XPathContext.FunctionArgType(i+1,"xbrl:xbrl")
    modelXbrl = xc.modelInstance(anytypeArg(xc, args, i, "xbrli:xbrl"))
    if modelXbrl:
        return modelXbrl
    raise XPathContext.FunctionArgType(i+1,"xbrl:xbrl")

def facts_in_instance(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    inst = instance(xc, p, args)
    return inst.factsInInstance

def items_in_instance(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    inst = instance(xc, p, args)
    return [f for f in inst.factsInInstance if f.isItem]

def tuples_in_instance(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    inst = instance(xc, p, args)
    return [f for f in inst.factsInInstance if f.isTuple]

def items_in_tuple(xc, p, args):
    raise xfiFunctionNotAvailable()

def tuples_in_tuple(xc, p, args):
    raise xfiFunctionNotAvailable()

def non_nil_facts_in_instance(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    inst = instance(xc, p, args)
    return [f for f in inst.factsInInstance if f.isItem and not f.isNil]

def concept(xc, p, args):
    qnConcept = qnameArg(xc, p, args, 0, 'QName', emptyFallback=None)
    srcConcept = xc.modelXbrl.qnameConcepts.get(qnConcept)
    if not (srcConcept and (srcConcept.isItem or srcConcept.isTuple)): 
        raise XPathContext.XPathException(p, 'xfie:invalidConceptQName', _('Argument 1 {0} is not a concept in the DTS.').format(qnConcept))
    return srcConcept

def concept_balance(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    return concept(xc,p,args).element.getAttributeNS(XbrlConst.xbrli, "balance")

def concept_period_type(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    return concept(xc,p,args).element.getAttributeNS(XbrlConst.xbrli, "periodType")

def concept_custom_attribute(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    qnAttr = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
    if not qnAttr: raise XPathContext.FunctionArgType(2,"xs:QName")
    element = concept(xc,p,args).element
    if qnAttr.namespaceURI:
        if not element.hasAttributeNS(qnAttr.namespaceURI, qnAttr.localName):
            return ()
        return xc.atomize(p, element.getAttributeNodeNS(qnAttr.namespaceURI, qnAttr.localName))
    else:
        if not element.hasAttribute(qnAttr.localName):
            return ()
        return xc.atomize(p, element.getAttributeNode(qnAttr.localName))

def concept_data_type(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    typeQname = concept(xc,p,args).typeQname
    if not typeQname or typeQname.localName.endswith(ModelObject.anonymousTypeSuffix):
        return ()
    return typeQname

def concept_data_type_derived_from(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    qnType = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
    if not qnType: raise XPathContext.FunctionArgType(2,"xs:QName")
    return concept(xc,p,args).instanceOfType(qnType)

def concept_substitutions(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    return concept(xc,p,args).substitutionGroupQnames

def filter_member_network_selection(xc, p, args):
    if len(args) != 5: raise XPathContext.FunctionNumArgs()
    qnDim = qnameArg(xc, p, args, 0, 'QName', emptyFallback=None)
    qnMem = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
    linkroleURI = stringArg(xc, args, 2, "xs:string")
    arcroleURI = stringArg(xc, args, 3, "xs:string")
    axis = stringArg(xc, args, 4, "xs:string")
    if not axis in ('descendant-or-self', 'child-or-self', 'descendant', 'child'):
        return ()
    dimConcept = xc.modelXbrl.qnameConcepts.get(qnDim)
    if not dimConcept or not dimConcept.isDimensionItem:
        raise XPathContext.XPathException(p, 'xfie:invalidDimensionQName', _('Argument 1 {0} is not a dimension concept QName.').format(qnDim))
    memConcept = xc.modelXbrl.qnameConcepts.get(qnMem)
    if not memConcept or not memConcept.isDomainMember:
        # removed error 2011-03-10: raise XPathContext.XPathException(p, 'xfie:unrecognisedExplicitDimensionValueQName', _('Argument 1 {0} is not a member concept QName.').format(qnMem))
        return ()
    relationshipSet = xc.modelXbrl.relationshipSet(arcroleURI, linkroleURI)
    if relationshipSet:
        members = set()
        linkQnames = set()
        arcQnames = set()
        if axis.endswith("-or-self"):
            members.add(qnMem)
        fromRels = relationshipSet.fromModelObject(memConcept)
        if fromRels:
            filter_member_network_members(relationshipSet, fromRels, axis.startswith("descendant"), members, linkQnames, arcQnames)
            ''' removed 2011-03-10:
            if len(linkQnames) > 1 or len(arcQnames) > 1:
                raise XPathContext.XPathException(p, 'xfie:ambiguousFilterMemberNetwork', 
                          _('Network of linkrole {0} and arcrole {1} dimension {2} from {3} is ambiguous because of multiple link elements, {4}, or arc elements {5}').format(
                            linkroleURI, arcroleURI, qnDim, qnMem, linkQnames, arcQnames))
            '''
            return members
        # no fromRels, must be a toRel or else the qname is not in the member network
        if relationshipSet.toModelObject(memConcept):
            return members  # valid situation, the member exists as a leaf node
    # removed error 2011-03-10: raise XPathContext.XPathException(p, 'xfie:unrecognisedExplicitDimensionValueQName', _('Argument 1 {0} member is not in the network.').format(qnMem))
    return ()

def filter_member_network_members(relationshipSet, fromRels, recurse, members, linkQnames, arcQnames):
    for modelRel in fromRels:
        toConcept = modelRel.toModelObject
        toConceptQname = toConcept.qname
        linkQnames.add(modelRel.linkQname)
        arcQnames.add(modelRel.qname)
        if toConceptQname not in members:
            members.add(toConceptQname)
            if recurse:
                filter_member_network_members(relationshipSet, relationshipSet.fromModelObject(toConcept), recurse, members, linkQnames, arcQnames)                

def fact_segment_remainder(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    context = item_context(xc, args)
    if context:
        return context.segNonDimValues
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def fact_scenario_remainder(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    context = item_context(xc, args)
    if context:
        return context.scenNonDimValues
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def fact_dim_value(xc, p, args, dimType):
    context = item_context(xc, args)
    qnDim = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
    dimConcept = xc.modelXbrl.qnameConcepts.get(qnDim)
    if not dimConcept or not dimConcept.isDimensionItem:
        raise XPathContext.XPathException(p, 
                                          'xfie:invalid{0}DimensionQName'.format(dimType), 
                                          _('Argument 1 {0} is not a dimension concept QName.').format(qnDim))
    if context:
        return context.dimValue(qnDim)
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def fact_has_explicit_dimension(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    dimValue = fact_dim_value(xc, p, args, "Explicit")
    return dimValue and (isinstance(dimValue,QName) or
                         dimValue.isExplicit)

def fact_has_typed_dimension(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    dimValue = fact_dim_value(xc, p, args, "Explicit")
    return dimValue and not isinstance(dimValue,QName) and dimValue.isTyped

def fact_explicit_dimension_value_value(xc, p, args):
    context = item_context(xc, args)
    if context:
        qn = qnameArg(xc, p, args, 1, 'QName', emptyFallback=())
        if qn == (): raise XPathContext.FunctionArgType(2,"xbrl:QName")
        dimConcept = xc.modelXbrl.qnameConcepts.get(qn) # check qname is explicit dimension
        if not dimConcept or not dimConcept.isExplicitDimension:
            raise XPathContext.XPathException(p, 'xfie:invalidExplicitDimensionQName', _('dimension does not specify an explicit dimension'))
        dimValue = context.dimValue(qn)
        if isinstance(dimValue, ModelObject.ModelDimensionValue) and dimValue.isExplicit:
            return dimValue.memberQname # known to be valid given instance is valid
        elif isinstance(dimValue, QName): #default, check if this is valid 
            ''' removed 2011-03-01 FWG clarification that default always applies
            modelItem = xc.modelItem(args[0][0])
            itemConcept = modelItem.concept
            from arelle.ValidateXbrlDimensions import checkPriItemDimValueValidity
            memConcept = xc.modelXbrl.qnameConcepts.get(dimValue)
            # remove check for pri item validity per FWG meeting notes 2011-01-13
            if itemConcept: # and checkPriItemDimValueValidity(xc, itemConcept, dimConcept, memConcept):
                return dimValue
            '''
            return dimValue
        return () # not an applicable primary item for default dimension
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def fact_has_explicit_dimension_value(xc, p, args):
    if len(args) != 3: raise XPathContext.FunctionNumArgs()
    return qnameArg(xc, p, args, 2, 'QName', emptyFallback=()) == fact_explicit_dimension_value_value(xc, p, args)

def fact_explicit_dimension_value(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    return fact_explicit_dimension_value_value(xc, p, args)

def fact_typed_dimension_value(xc, p, args):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    context = item_context(xc, args)
    if context:
        qn = qnameArg(xc, p, args, 1, 'QName', emptyFallback=())
        if qn == (): raise XPathContext.FunctionArgType(2,"xbrl:QName")
        modelConcept = xc.modelXbrl.qnameConcepts.get(qn) # check qname is explicit dimension
        if not modelConcept or not modelConcept.isTypedDimension:
            raise XPathContext.XPathException(p, 'xfie:invalidTypedDimensionQName', _('dimension does not specify a typed dimension'))
        result = context.dimValue(qn)
        return result.typedMember if result else ()
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def fact_dimension_s_equal2(xc, p, args):
    if len(args) != 3: raise XPathContext.FunctionNumArgs()
    context1 = item_context(xc, args, i=0)
    context2 = item_context(xc, args, i=1)
    if context1:
        if context2:
            qn = qnameArg(xc, p, args, 2, 'QName', emptyFallback=())
            if qn == (): raise XPathContext.FunctionArgType(3,"xbrl:QName")
            modelConcept = xc.modelXbrl.qnameConcepts.get(qn) # check qname is explicit dimension
            if not modelConcept or not modelConcept.isTypedDimension:
                # raise XPathContext.XPathException(p, 'xfie:invalidTypedDimensionQName', _('dimension does not specify a typed dimension'))
                return False
            dimValue1 = context1.dimValue(qn)
            dimValue2 = context1.dimValue(qn)
            if dimValue1 and isinstance(dimValue1,ModelObject.ModelDimensionValue):
                    return dimValue1.isEqualTo(dimValue2)
            elif dimValue2 and isinstance(dimValue2,ModelObject.ModelDimensionValue):
                    return dimValue2.isEqualTo(dimValue1)
            return dimValue1 == dimValue2
        raise XPathContext.FunctionArgType(2,"xbrl:item")
    raise XPathContext.FunctionArgType(1,"xbrl:item")

def linkbase_link_roles(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    arcroleURI = stringArg(xc, args, 0, "xs:string")
    relationshipSet = xc.modelXbrl.relationshipSet(arcroleURI)
    if relationshipSet:
        return [anyURI(linkrole) for linkrole in relationshipSet.linkRoleUris]
    return ()

def navigate_relationships(xc, p, args):
    raise xfiFunctionNotAvailable()

def concept_label(xc, p, args):
    if len(args) == 5: raise xfiFunctionNotAvailable()
    if len(args) != 4: raise XPathContext.FunctionNumArgs()
    qnSource = qnameArg(xc, p, args, 0, 'QName', emptyFallback=None)
    srcConcept = xc.modelXbrl.qnameConcepts.get(qnSource)
    if not srcConcept:
        return ""
    linkroleURI = stringArg(xc, args, 1, "xs:string", emptyFallback='')
    if not linkroleURI: linkroleURI = XbrlConst.defaultLinkRole
    labelroleURI = stringArg(xc, args, 2, "xs:string", emptyFallback='')
    if not labelroleURI: labelroleURI = XbrlConst.standardLabel
    lang = stringArg(xc, args, 3, "xs:string", emptyFallback='')
    relationshipSet = xc.modelXbrl.relationshipSet(XbrlConst.conceptLabel,linkroleURI)
    if relationshipSet:
        label = relationshipSet.label(srcConcept, labelroleURI, lang)
        if label is not None: return label
    return ""


def arcrole_definition(xc, p, args):
    if len(args) == 2: raise XPathContext.FunctionNumArgs()
    arcroleURI = stringArg(xc, args, 0, "xs:string", emptyFallback='')
    modelArcroleTypes = xc.modelXbrl.arcroleTypes.get(arcroleURI)
    if modelArcroleTypes is not None and len(modelArcroleTypes) > 0:
        arcroledefinition = modelArcroleTypes[0].definition
        if arcroledefinition is not None: return arcroledefinition
    return ()

def role_definition(xc, p, args):
    roleURI = stringArg(xc, args, 0, "xs:string", emptyFallback='')
    modelRoleTypes = xc.modelXbrl.roleTypes.get(roleURI)
    if modelRoleTypes is not None and len(modelRoleTypes) > 0:
        roledefinition = modelRoleTypes[0].definition
        if roledefinition is not None: return roledefinition
    return ()

def fact_footnotes(xc, p, args):
    if len(args) != 5: raise XPathContext.FunctionNumArgs()
    itemObj = item(xc, args)
    linkroleURI = stringArg(xc, args, 1, "xs:string", emptyFallback='')
    if not linkroleURI: linkroleURI = XbrlConst.defaultLinkRole
    arcroleURI = stringArg(xc, args, 2, "xs:string", emptyFallback='')
    if not arcroleURI: arcroleURI = XbrlConst.factFootnote
    footnoteroleURI = stringArg(xc, args, 3, "xs:string", emptyFallback='')
    if not footnoteroleURI: footnoteroleURI = XbrlConst.footnote
    lang = stringArg(xc, args, 4, "xs:string", emptyFallback='')
    relationshipSet = xc.modelXbrl.relationshipSet(arcroleURI,linkroleURI)
    if relationshipSet:
        return relationshipSet.label(itemObj, footnoteroleURI, lang, returnMultiple=True)
    return ()

def concept_relationships(xc, p, args):
    lenArgs = len(args)
    if lenArgs < 4 or lenArgs > 8: raise XPathContext.FunctionNumArgs()
    qnSource = qnameArg(xc, p, args, 0, 'QName', emptyFallback=None)
    linkroleURI = stringArg(xc, args, 1, "xs:string")
    if not linkroleURI:
        linkroleURI = XbrlConst.defaultLinkRole
    arcroleURI = stringArg(xc, args, 2, "xs:string")
    axis = stringArg(xc, args, 3, "xs:string")
    if not axis in ('descendant', 'child', 'ancestor', 'parent', 'sibling', 'sibling-or-self'):
        return ()
    if qnSource != XbrlConst.qnXfiRoot:
        srcConcept = xc.modelXbrl.qnameConcepts.get(qnSource)
        if not srcConcept:
            return ()
    if lenArgs > 4:
        generations = numericArg(xc, p, args, 4, "xs:integer", convertFallback=0)
    elif axis in ('child', 'parent', 'sibling', 'sibling-or-self'):
        generations = 1
    else:
        generations = 0
    if axis in ('child','parent','sibling', 'sibling-or-self'):
        generations = 1
    if axis == 'child':
        axis = 'descendant'
    elif axis == 'parent':
        axis = 'ancestor'
    if lenArgs > 5:
        qnLink = qnameArg(xc, p, args, 5, 'QName', emptyFallback=None)
    else:
        qnLink = None
    if lenArgs > 5:
        qnArc = qnameArg(xc, p, args, 6, 'QName', emptyFallback=None)
    else:
        qnArc = None
        
    removeSelf = axis == 'sibling'
    relationshipSet = xc.modelXbrl.relationshipSet(arcroleURI, linkroleURI, qnLink, qnArc)
    if relationshipSet:
        result = []
        visited = {qnSource}
        if qnSource == XbrlConst.qnXfiRoot:
            if axis in ('sibling', 'sibling-or-self', 'ancestor'):
                return []
            roots = relationshipSet.rootConcepts
            visited = {c.qname for c in roots}
            rels = [rel for c in roots for rel in relationshipSet.fromModelObject(c)]
            if generations == 1:
                return rels
            if generations > 1:
                generations -= 1
        elif axis == 'descendant':
            rels = relationshipSet.fromModelObject(srcConcept)
        elif axis == 'ancestor': # includes first pass on parents of object to get sibling
            rels = relationshipSet.toModelObject(srcConcept)
        elif axis in ('sibling', 'sibling-or-self'):
            rels = relationshipSet.toModelObject(srcConcept)
            if rels:
                rels = relationshipSet.fromModelObject(rels[0].fromModelObject)
                axis = 'descendant'
            else: # must be a root, never has any siblings
                return []
        if rels:
            concept_relationships_step(xc, relationshipSet, rels, axis, generations, result, visited)
            if removeSelf:
                for i, rel in enumerate(result):
                    if rel.toModelObject == srcConcept:
                        result.pop(i)
                        break
            return result
    return ()

def concept_relationships_step(xc, relationshipSet, rels, axis, generations, result, visited):
    for modelRel in rels:
        concept = modelRel.toModelObject if axis == 'descendant' else modelRel.fromModelObject
        conceptQname = concept.qname
        result.append(modelRel)
        if generations > 1 or (generations == 0 and conceptQname not in visited):
            nextGen = (generations - 1) if generations > 1 else 0
            if generations == 0:
                visited.add(conceptQname)
            if axis in ('descendant'):
                stepRels = relationshipSet.fromModelObject(concept)
            else:
                stepRels = relationshipSet.toModelObject(concept)
            concept_relationships_step(xc, relationshipSet, stepRels, axis, nextGen, result, visited)
            if generations == 0:
                visited.discard(conceptQname)

def relationship_from_concept(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    modelRel = anytypeArg(xc, args, 0, "arelle:ModelRelationship", None)
    if modelRel:
        return modelRel.fromModelObject.qname
    raise XPathContext.FunctionArgType(1,"arelle:modelRelationship")

def relationship_to_concept(xc, p, args):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    modelRel = anytypeArg(xc, args, 0, "arelle:ModelRelationship", None)
    if modelRel:
        return modelRel.toModelObject.qname
    raise XPathContext.FunctionArgType(1,"arelle:modelRelationship")

def distinct_nonAbstract_parent_concepts(xc, p, args):
    raise xfiFunctionNotAvailable()

def element_attribute(xc, p, args, elementParent=False):
    if len(args) != 2: raise XPathContext.FunctionNumArgs()
    modelRel = anytypeArg(xc, args, 0, "arelle:ModelRelationship", None)
    if not modelRel: raise XPathContext.FunctionArgType(1,"arelle:modelRelationship")
    qnAttr = qnameArg(xc, p, args, 1, 'QName', emptyFallback=None)
    if not qnAttr: raise XPathContext.FunctionArgType(2,"xs:QName")
    element = modelRel.element
    if elementParent: element = element.parentNode
    if qnAttr.namespaceURI:
        if not element.hasAttributeNS(qnAttr.namespaceURI, qnAttr.localName):
            return ()
        return xc.atomize(p, element.getAttributeNodeNS(qnAttr.namespaceURI, qnAttr.localName))
    else:
        if not element.hasAttribute(qnAttr.localName):
            return ()
        return xc.atomize(p, element.getAttributeNode(qnAttr.localName))
   
def relationship_attribute(xc, p, args):
    return element_attribute(xc, p, args)

def relationship_link_attribute(xc, p, args):
    return element_attribute(xc, p, args, elementParent=True)

def element_name(xc, p, args, elementParent=False):
    if len(args) != 1: raise XPathContext.FunctionNumArgs()
    modelRel = anytypeArg(xc, args, 0, "arelle:ModelRelationship", None)
    if not modelRel: raise XPathContext.FunctionArgType(1,"arelle:modelRelationship")
    element = modelRel.element
    if elementParent: element = element.parentNode
    return qname(element)

def relationship_name(xc, p, args):
    return element_name(xc, p, args)

def relationship_link_name(xc, p, args):
    return element_name(xc, p, args, elementParent=True)

def xbrl_instance(xc, p, args):
    raise xfiFunctionNotAvailable()

def  format_number(xc, p, args):
    raise xfiFunctionNotAvailable()

xfiFunctions = {
    'context': context,
    'unit': unit,
    'unit-numerator': unit_numerator,
    'unit-denominator': unit_denominator,
    'measure-name': measure_name,
    'period': period,
    'context-period': context_period,
    'is-start-end-period': is_start_end_period,
    'is-forever-period': is_forever_period,
    'is-duration-period': is_duration_period,
    'is-instant-period': is_instant_period,
    'period-start': period_start,
    'period-end': period_end,
    'period-instant': period_instant,
    'entity' : entity,
    'context-entity' : context_entity,
    'identifier': identifier,
    'context-identifier': context_identifier,
    'entity-identifier': entity_identifier,
    'identifier-value': identifier_value,
    'identifier-scheme': identifier_scheme,
    'segment': segment,
    'entity-segment': entity_segment,
    'context-segment': context_segment,
    'scenario': scenario,
    'context-scenario': context_scenario,
    'fact-identifier-value': fact_identifier_value,
    'fact-identifier-scheme': fact_identifier_scheme,
    'is-non-numeric' : non_numeric,
    'is-numeric' : numeric,
    'is-fraction' : fraction,
    'precision': precision,
    'decimals': decimals,
    'uncovered-aspect' : uncovered_aspect,
    'identical-nodes': identical_nodes,
    's-equal': s_equal,
    'u-equal': u_equal,
    'v-equal': v_equal,
    'c-equal': c_equal,
    'identical-node-set' : identical_node_set,
    's-equal-set': s_equal_set,
    'v-equal-set': v_equal_set,
    'c-equal-set': c_equal_set,
    'u-equal-set': u_equal_set,
    'x-equal': x_equal,
    'duplicate-item': duplicate_item,
    'duplicate-tuple': duplicate_tuple,
    'p-equal': p_equal,
    'cu-equal': cu_equal,
    'pc-equal': pc_equal,
    'pcu-equal': pcu_equal,
    'start-equal': start_equal,
    'end-equal': end_equal,
    'nodes-correspond': nodes_correspond,
    'facts-in-instance': facts_in_instance,
    'items-in-instance': items_in_instance,
    'tuples-in-instance': tuples_in_instance,
    'items-in-tuple': items_in_tuple,
    'tuples-in-tuple': tuples_in_tuple,
    'non-nil-facts-in-instance': non_nil_facts_in_instance,
    'concept-balance': concept_balance,
    'concept-period-type': concept_period_type,
    'concept-custom-attribute': concept_custom_attribute,
    'concept-data-type': concept_data_type,
    'concept-data-type-derived-from' : concept_data_type_derived_from,
    'concept-substitutions': concept_substitutions,
    'filter-member-network-selection' : filter_member_network_selection,
    'fact-segment-remainder': fact_segment_remainder,
    'fact-scenario-remainder': fact_scenario_remainder,
    'fact-has-explicit-dimension': fact_has_explicit_dimension,
    'fact-has-typed-dimension': fact_has_typed_dimension,
    'fact-has-explicit-dimension-value': fact_has_explicit_dimension_value,
    'fact-explicit-dimension-value': fact_explicit_dimension_value,
    'fact-typed-dimension-value': fact_typed_dimension_value,
    'fact-dimension-s-equal2': fact_dimension_s_equal2,
    'linkbase-link-roles': linkbase_link_roles,
    'concept-label': concept_label,
    'arcrole-definition': arcrole_definition,
    'role-definition': role_definition,
    'fact-footnotes': fact_footnotes,
    'concept-relationships': concept_relationships,
    'relationship-from-concept': relationship_from_concept,
    'relationship-to-concept': relationship_to_concept,
    'distinct-nonAbstract-parent-concepts': distinct_nonAbstract_parent_concepts,
    'relationship-attribute': relationship_attribute,
    'relationship-link-attribute': relationship_link_attribute,
    'relationship-name': relationship_name,
    'relationship-link-name': relationship_link_name,
    'xbrl-instance': xbrl_instance,
    'format-number':  format_number,
     }

