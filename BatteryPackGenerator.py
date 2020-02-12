#Author- Queron Williams ( @Ducktaperules )
#Description-script for generating 18650 battery packs

import adsk.core, adsk.fusion, adsk.cam, traceback
import math

_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_units = 'mm'


_cellWidth = adsk.core.ValueCommandInput.cast(None)
_cellHeight = adsk.core.ValueCommandInput.cast(None)
_cellSpacing = adsk.core.ValueCommandInput.cast(None)
_packSCount = adsk.core.StringValueCommandInput.cast(None)
_packPCount = adsk.core.StringValueCommandInput.cast(None)
_stagger = adsk.core.DropDownCommandInput.cast(None)


_errMessage = adsk.core.TextBoxCommandInput.cast(None)

_handlers = []

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface

        cmdDef = _ui.commandDefinitions.itemById('adskBatteryPackPythonScript')
        if not cmdDef:
            # Create a command definition.
            # removed cause broken # cmdDef = _ui.commandDefinitions.addButtonDefinition('adskBatteryPackPythonScript', 'BatteryPack', 'Creates a BatteryPack component', 'Resources/BatteryPack') 
            cmdDef = _ui.commandDefinitions.addButtonDefinition('adskBatteryPackPythonScript', 'BatteryPack', 'Creates a BatteryPack component', '') 

        # Connect to the command created event.
        onCommandCreated = BatteryPackCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)
        
        # Execute the command.
        cmdDef.execute()

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class BatteryPackCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Verfies that a value command input has a valid expression and returns the 
# value if it does.  Otherwise it returns False.  This works around a 
# problem where when you get the value from a ValueCommandInput it causes the
# current expression to be evaluated and updates the display.  Some new functionality
# is being added in the future to the ValueCommandInput object that will make 
# this easier and should make this function obsolete.
def getCommandInputValue(commandInput, unitType):
    try:
        valCommandInput = adsk.core.ValueCommandInput.cast(commandInput)
        if not valCommandInput:
            return (False, 0)

        # Verify that the expression is valid.
        des = adsk.fusion.Design.cast(_app.activeProduct)
        unitsMgr = des.unitsManager
        
        if unitsMgr.isValidExpression(valCommandInput.expression, unitType):
            value = unitsMgr.evaluateExpression(valCommandInput.expression, unitType)
            return (True, value)
        else:
            return (False, 0)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



# Event handler for the commandCreated event.
class BatteryPackCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            
            # Verify that a Fusion design is active.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            if not des:
                _ui.messageBox('A Fusion design must be active when invoking this command.')
                return()

            cellWidth = str(1.8)
            cellWidthAttrib = des.attributes.itemByName('BatteryPack', 'cellWidth')
            if cellWidthAttrib:
                cellWidth = cellWidthAttrib.value

            cellHeight = str(6.5)
            cellHeightAttrib = des.attributes.itemByName('BatteryPack', 'cellHeight')
            if cellHeightAttrib:
                cellHeight = cellHeightAttrib.value

            cellSpacing = str(2)
            cellSpacingAttrib = des.attributes.itemByName('BatteryPack', 'cellSpacing')
            if cellSpacingAttrib:
                cellSpacing = cellSpacingAttrib.value

            packSCount = '12'
            packSCountAttrib = des.attributes.itemByName('BatteryPack', 'packSCount')
            if packSCountAttrib:
                packSCount = packSCountAttrib.value

            packPCount = '8'
            packPCountAttrib = des.attributes.itemByName('BatteryPack', 'packPCount')
            if packPCountAttrib:
                packPCount = packPCountAttrib.value

            cmd = eventArgs.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs
            
            global _cellWidth, _cellHeight, _cellSpacing, _packSCount, _packPCount, _stagger, _errMessage

            _cellWidth = inputs.addValueInput('cellWidth', 'Cell Width', _units, adsk.core.ValueInput.createByReal(float(cellWidth)))
            _cellHeight = inputs.addValueInput('cellHeight', 'Cell Height', _units, adsk.core.ValueInput.createByReal(float(cellHeight)))
            _cellSpacing = inputs.addValueInput('cellSpacing', 'Cell Spacing', _units, adsk.core.ValueInput.createByReal(float(cellSpacing)))
            _packSCount = inputs.addStringValueInput('packSCount', 'Pack S Count', packSCount)
            _packPCount = inputs.addStringValueInput('packPCount', 'Pack P Count', packPCount)
            _stagger = inputs.addDropDownCommandInput('stagger', 'Stagger Cells', adsk.core.DropDownStyles.TextListDropDownStyle)
            _stagger.listItems.add('None', True)
            _stagger.listItems.add('Stagger Series', False)
            _stagger.listItems.add('Stagger Parallel', False)
            
            _errMessage = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
            _errMessage.isFullWidth = True
            
            # Connect to the command related events.
            onExecute = BatteryPackCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)        
            
            onInputChanged = BatteryPackCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)     
            
            onValidateInputs = BatteryPackCommandValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

            onDestroy = BatteryPackCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the execute event.
class BatteryPackCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Save the current values as attributes.
            des = adsk.fusion.Design.cast(_app.activeProduct)
            attribs = des.attributes
            attribs.add('BatteryPack', 'cellWidth', str(_cellWidth.value))
            attribs.add('BatteryPack', 'cellHeight', str(_cellHeight.value))
            attribs.add('BatteryPack', 'cellSpacing', str(_cellSpacing.value))
            attribs.add('BatteryPack', 'packSCount', str(_packSCount.value))
            attribs.add('BatteryPack', 'packPCount', str(_packPCount.value))
            attribs.add('BatteryPack', 'stagger', _stagger.selectedItem.name)

            cellWidth = _cellWidth.value
            cellHeight = _cellHeight.value
            cellSpacing = _cellSpacing.value
            packSCount = int(_packSCount.value)
            packPCount = int(_packPCount.value)

            stagger = None
            if _stagger.selectedItem.name == 'None':
                stagger = 0
            elif _stagger.selectedItem.name == 'Stagger Series':
                stagger = 1
            elif _stagger.selectedItem.name == 'Stagger Parallel':
                stagger = 2

            # Create the BatteryPack.
            batteryPackComp = drawBatteryPack(cellWidth, cellHeight, cellSpacing, packSCount, packPCount, stagger)
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
 
# Event handler for the inputChanged event.
class BatteryPackCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            changedInput = eventArgs.input
            
            global _units
            # Set each one to it's current value because otherwised if the user 
            # has edited it, the value won't update in the dialog because 
            # apparently it remembers the units when the value was edited.
            # Setting the value using the API resets this.
            _cellWidth.value = _cellWidth.value
            _cellHeight.value = _cellHeight.value
            _cellSpacing.value = _cellSpacing.value
            _packSCount.value = _packSCount.value
            _packPCount.value = _packPCount.value
            _stagger.selectedItem.name = _stagger.selectedItem.name 
                            
        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        
# Event handler for the validateInputs event.
class BatteryPackCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
            
            _errMessage.text = ''

            # # Verify that at lesat 4 teath are specified.
            # if not _numTeeth.value.isdigit():
            #     _errMessage.text = 'The number of teeth must be a whole number.'
            #     eventArgs.areInputsValid = False
            #     return
            # else:    
            #     numTeeth = int(_numTeeth.value)
            

            des = adsk.fusion.Design.cast(_app.activeProduct)

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
       

# Builds a BatteryPack.
def drawBatteryPack(cellWidth, cellHeight, cellSpacing, packSCount, packPCount, stagger):
    try:

        design = _app.activeProduct

        # Get the root component of the active design.
        rootComp = design.rootComponent

        # Create a component under root component
        occ1 = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ1.component.name = '{}s{}p Pack'.format(packSCount, packPCount)
        pack = occ1.component

        # Create a new sketch on the xz plane.
        sketches = pack.sketches
        xzPlane = pack.xZConstructionPlane
        sketchCells = sketches.add(xzPlane)
        sketchCells.name = 'Layout'

        #some usefull numbers
        cellSpacingX = cellSpacing
        cellSpacingY = cellSpacing
        cellOffsetX = 0
        cellOffsetY = 0
        noOfCells = packSCount*packPCount

        if stagger == 1:
            cellSpacingX = cellSpacing* math.sin(math.radians(60))
            cellOffsetY = cellSpacing* math.cos(math.radians(60))
        if stagger == 2:
            cellSpacingY = cellSpacing* math.sin(math.radians(60))
            cellOffsetX = cellSpacing* math.cos(math.radians(60))

        startOffsetX = cellSpacingX*(packSCount-1)/2
        startOffsetY = cellSpacingY*(packPCount-1)/2
        
        # Draw some circles.
        circles = sketchCells.sketchCurves.sketchCircles

        for x in range(0, packSCount):
            if (x % 2) == 0:
                yBump = cellOffsetY/2
            else:
                yBump = -cellOffsetY/2

            for y in range(0, packPCount):
                if (y % 2) == 0:
                    xBump = cellOffsetX/2
                else:
                    xBump = -cellOffsetX/2
                
                circle1 = circles.addByCenterRadius(adsk.core.Point3D.create( -startOffsetX + x*cellSpacingX + xBump, -startOffsetY + y*cellSpacingY + yBump, 0), cellWidth/2)

        
        # Get extrude features
        cellsExtrude = pack.features.extrudeFeatures
        distance = adsk.core.ValueInput.createByReal(cellHeight)

        profs = adsk.core.ObjectCollection.create()
        for prof in sketchCells.profiles:
            profs.add(prof)    
        extrude1 = cellsExtrude.addSimple(profs, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation )


        _ui.messageBox('"Buy me a pint someday" - @ducktaperules')

    except:
        _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))