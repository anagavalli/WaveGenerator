import maya.cmds as cmds
import pymel.core as pm
import BossEditor as boss
import mtoa.utils
import mtoa.core #/Applications/solidangle/mtoa/2019/scripts/mtoa/core.py

cmds.requires('Boss', '2.0.1.0', nodeType=['BossBlender', 'BossSpectralWave'])
cmds.requires('lookdevKit', '1.0', nodeType=['colorMath'])
cmds.requires('mtoa', '3.2.2')
cmds.requires('OpenEXRLoader', '2012')

# Taken from BossEditor module, with references to UI window removed.
def createBossCache ( nodes, playblastMode ):
    # first check the input nodes to see whether they are cachable or not
    # also remove disabled nodes from the list
    cachableNodes = boss.getAllCachableNodes()
    # clean input nodes
    for node in nodes[:]:
        if ( node not in cachableNodes ) or ( not pm.getAttr( node + ".enable" ) ):
            nodes.remove( node )

    # if there is nothing to cache return
    if len( nodes ) == 0:
        return

    for node in nodes:
        print "[Boss] Preparing node " + node + " for caching..."
        # first turn off use cache for the node
        pm.setAttr ( node + ".useCache", False )
        #set export cache flag for the node to true
        pm.setAttr ( node + ".exportCache", True)

    # depending on cachetype enable disable objects so that we have faster caching
    switchableNodes = boss.getAllSwitchableBossNodes()
    solverNodes = boss.getSolvers()
    enableStates = dict ()

    # we need to cache selected solver only
    # so disable everything not related to that solver
    nodesToCache = boss.getSolverInfluences( nodes[ 0 ] ) + nodes

    # we only need to cache selected/enabled nodes
    for switchableNode in switchableNodes:
        if switchableNode not in nodesToCache:
            if switchableNode in solverNodes:
                # this is a solver node
                # instead of enable flag use bossExport
                pm.setAttr( switchableNode + ".bossExport", True )
            else:
                # get enable state and store it so that we can revert back
                enableStates[ switchableNode ] = pm.getAttr( switchableNode + ".enable" )

                # if this node is not in the list of what we need to cache disable it
                if switchableNode not in nodes:
                    pm.setAttr( switchableNode + ".enable", False )

    startTime, endTime = boss.getTimeRangeForCaching()
    evaluateEvery = boss.getEvaluateEvery()
    saveEvery = boss.getSaveEvery()

    print "[Boss] Caching between frames", startTime, endTime, "at every", evaluateEvery

    # setup progress bar
    gMainProgressBar = pm.mel.eval('$tmp = $gMainProgressBar')

    pm.progressBar( gMainProgressBar,
                    edit = True,
                    beginProgress = True,
                    isInterruptable = True,
                    status = 'Caching Boss...',
                    minValue = startTime,
                    maxValue = endTime )

    frame = startTime
    while ( frame <= endTime ):
        if pm.progressBar ( gMainProgressBar, query = True, isCancelled = True ):
            break
        pm.currentTime ( frame )
        frame += evaluateEvery
        pm.progressBar(gMainProgressBar, edit = True, step = evaluateEvery )

    # we are done
    pm.progressBar( gMainProgressBar, edit = True, endProgress = True )

    for node in nodes:
        # first turn on use cache for the node
        pm.setAttr ( node + ".useCache", True )

        #set export cache flag for the node to false
        pm.setAttr ( node + ".exportCache", False )

    # revert to pre cache enable state
    solvers = boss.getSolvers()
    for solver in solvers:
        pm.setAttr( solver + ".bossExport", False )

    for switchableNode in enableStates.keys():
        pm.setAttr( switchableNode + ".enable", enableStates[ switchableNode ] )

def createFileTexture(imagePath, fileTextureName, p2dName):
    tex = pm.shadingNode('file', name=fileTextureName, asTexture=True, isColorManaged=True)
    if not pm.objExists(p2dName):
        p2d = pm.shadingNode('place2dTexture', name=p2dName, asUtility=True)
    tex.filterType.set(0)

    pm.connectAttr(p2d.outUV, tex.uvCoord)
    pm.connectAttr(p2d.outUvFilterSize, tex.uvFilterSize)
    pm.connectAttr(p2d.vertexCameraOne, tex.vertexCameraOne)
    pm.connectAttr(p2d.vertexUvOne, tex.vertexUvOne)
    pm.connectAttr(p2d.vertexUvThree, tex.vertexUvThree)
    pm.connectAttr(p2d.vertexUvTwo, tex.vertexUvTwo)
    pm.connectAttr(p2d.coverage, tex.coverage)
    pm.connectAttr(p2d.mirrorU, tex.mirrorU)
    pm.connectAttr(p2d.mirrorV, tex.mirrorV)
    pm.connectAttr(p2d.noiseUV, tex.noiseUV)
    pm.connectAttr(p2d.offset, tex.offset)
    pm.connectAttr(p2d.repeatUV, tex.repeatUV)
    pm.connectAttr(p2d.rotateFrame, tex.rotateFrame)
    pm.connectAttr(p2d.rotateUV, tex.rotateUV)
    pm.connectAttr(p2d.stagger, tex.stagger)
    pm.connectAttr(p2d.translateFrame, tex.translateFrame)
    pm.connectAttr(p2d.wrapU, tex.wrapU)
    pm.connectAttr(p2d.wrapV, tex.wrapV)

    pm.setAttr(tex+'.ftn', imagePath, type='string')
    pm.setAttr(tex+'.cs', 'Raw', type='string')

    return tex

def setWaterShaderAttributes(nodeName):
    #/Applications/solidangle/mtoa/2019/presets/attrPresets/aiStandardSurface/Deep_Water.mel
    pm.setAttr(nodeName+".frozen", 0)
    pm.setAttr(nodeName+".aiEnableMatte", 0)
    pm.setAttr(nodeName+".aiMatteColorR", 0)
    pm.setAttr(nodeName+".aiMatteColorG", 0)
    pm.setAttr(nodeName+".aiMatteColorB", 0)
    pm.setAttr(nodeName+".aiMatteColorA", 0)
    pm.setAttr(nodeName+".base", 0)
    pm.setAttr(nodeName+".baseColorR", 0.1860000044)
    pm.setAttr(nodeName+".baseColorG", 0.1860000044)
    pm.setAttr(nodeName+".baseColorB", 0.1860000044)
    pm.setAttr(nodeName+".diffuseRoughness", 0)
    pm.setAttr(nodeName+".specular", 1)
    pm.setAttr(nodeName+".specularColorR", 1)
    pm.setAttr(nodeName+".specularColorG", 1)
    pm.setAttr(nodeName+".specularColorB", 1)
    pm.setAttr(nodeName+".specularRoughness", 0.1199999973)
    pm.setAttr(nodeName+".specularIOR", 1.332999945)
    pm.setAttr(nodeName+".specularAnisotropy", 0)
    pm.setAttr(nodeName+".specularRotation", 0)
    pm.setAttr(nodeName+".metalness", 0)
    pm.setAttr(nodeName+".transmission", 1)
    pm.setAttr(nodeName+".transmissionColorR", 0.743999958)
    pm.setAttr(nodeName+".transmissionColorG", 0.9400832057)
    pm.setAttr(nodeName+".transmissionColorB", 1)
    pm.setAttr(nodeName+".transmissionDepth", 10)
    pm.setAttr(nodeName+".transmissionScatterR", 0.06749999523)
    pm.setAttr(nodeName+".transmissionScatterG", 0.1340401471)
    pm.setAttr(nodeName+".transmissionScatterB", 0.5)
    pm.setAttr(nodeName+".transmissionScatterAnisotropy", 0.75)
    pm.setAttr(nodeName+".transmissionDispersion", 0)
    pm.setAttr(nodeName+".transmissionExtraRoughness", 0)
    pm.setAttr(nodeName+".subsurface", 0)
    pm.setAttr(nodeName+".subsurfaceColorR", 1)
    pm.setAttr(nodeName+".subsurfaceColorG", 1)
    pm.setAttr(nodeName+".subsurfaceColorB", 1)
    pm.setAttr(nodeName+".subsurfaceRadiusR", 1)
    pm.setAttr(nodeName+".subsurfaceRadiusG", 1)
    pm.setAttr(nodeName+".subsurfaceRadiusB", 1)
    pm.setAttr(nodeName+".subsurfaceScale", 1)
    pm.setAttr(nodeName+".thinWalled", 0)
    pm.setAttr(nodeName+".tangentX", 0)
    pm.setAttr(nodeName+".tangentY", 0)
    pm.setAttr(nodeName+".tangentZ", 0)
    pm.setAttr(nodeName+".coat", 0)
    pm.setAttr(nodeName+".coatColorR", 1)
    pm.setAttr(nodeName+".coatColorG", 1)
    pm.setAttr(nodeName+".coatColorB", 1)
    pm.setAttr(nodeName+".coatRoughness", 0.1000000015)
    pm.setAttr(nodeName+".coatIOR", 1.5)
    pm.setAttr(nodeName+".coatNormalX", 0)
    pm.setAttr(nodeName+".coatNormalY", 0)
    pm.setAttr(nodeName+".coatNormalZ", 0)
    pm.setAttr(nodeName+".emission", 0)
    pm.setAttr(nodeName+".emissionColorR", 1)
    pm.setAttr(nodeName+".emissionColorG", 1)
    pm.setAttr(nodeName+".emissionColorB", 1)
    pm.setAttr(nodeName+".opacityR", 1)
    pm.setAttr(nodeName+".opacityG", 1)
    pm.setAttr(nodeName+".opacityB", 1)
    pm.setAttr(nodeName+".caustics", 0)
    pm.setAttr(nodeName+".internalReflections", 1)
    pm.setAttr(nodeName+".exitToBackground", 0)
    pm.setAttr(nodeName+".indirectDiffuse", 1)
    pm.setAttr(nodeName+".indirectSpecular", 1)

def generateHiDefOcean(oceanHeight, oceanWidth, numSubDiv, backgroundFile):
    # Set up high fidelity polys
    hiFiOceanTransform, hiFiOceanNode = pm.polyPlane(name='highFidelityOcean', height=60, width=60, axis=[0,1,0], subdivisionsWidth=1024, subdivisionsHeight=1024)
    hiFiOceanShape = pm.listRelatives(hiFiOceanTransform, children=True, type='mesh')[0]
    pm.setAttr(hiFiOceanTransform+'.visibility', False)

    # Create BOSS nodes
    mainSpectralWave = pm.createNode('BossSpectralWave', name='BossMainSpectralWave#')

    pm.setAttr(mainSpectralWave+'.startFrame', 1)
    pm.setAttr(mainSpectralWave+'.patchSizeX', 130)
    pm.setAttr(mainSpectralWave+'.patchSizeZ', 130)
    pm.setAttr(mainSpectralWave+'.resolutionX', 1024)
    pm.setAttr(mainSpectralWave+'.resolutionZ', 1024)
    pm.setAttr(mainSpectralWave+'.waveSize', 2.8)
    pm.setAttr(mainSpectralWave+'.windSpeed', 4) 
    pm.setAttr(mainSpectralWave+'.enableFoam', True)
    pm.setAttr(mainSpectralWave+'.cuspMin', 0.005)
    pm.setAttr(mainSpectralWave+'.useDisplacement', True)
    pm.setAttr(mainSpectralWave+'.useCache', True)

    subSpectralWave = pm.createNode('BossSpectralWave', name='BossSubSpectralWave#')

    pm.setAttr(subSpectralWave+'.startFrame', 1)
    pm.setAttr(subSpectralWave+'.patchSizeX', 70)
    pm.setAttr(subSpectralWave+'.patchSizeZ', 70)
    pm.setAttr(subSpectralWave+'.resolutionX', 1024)
    pm.setAttr(subSpectralWave+'.resolutionZ', 1024)
    pm.setAttr(subSpectralWave+'.useCache', True)

    bossBlender = pm.createNode('BossBlender', name='BossBlender#')

    pm.setAttr(bossBlender+'.inwave', size=2)
    pm.setAttr(bossBlender+'.solvers', size=2)

    bossTransform = pm.createNode('transform', name='BossTransform#')
    bossOutput = pm.createNode('mesh', name='BossOutputShape#', parent=bossTransform)

    pm.setAttr(bossOutput+'.v', keyable=False)
    pm.setAttr(bossOutput+'.vir', True)
    pm.setAttr(bossOutput+'.vif', True)
    pm.setAttr(bossOutput+'.uvst[0].uvsn', 'map1', type='string')
    pm.setAttr(bossOutput+'.cuvs', 'map1', type='string')
    pm.setAttr(bossOutput+'.dcc', 'Ambient+Diffuse', type='string')
    pm.setAttr(bossOutput+'.covm[0]', 0, 1, 1)
    pm.setAttr(bossOutput+'.cdvm[0]', 0, 1, 1)
    pm.setAttr(bossOutput+'.ai_translator', 'polymesh', type='string')
    
    # Link up nodes
    pm.connectAttr(bossBlender+'.outMesh', bossOutput+'.i')

    pm.connectAttr(hiFiOceanShape+'.w', bossBlender+'.inMesh')
    pm.connectAttr(':time1.o', bossBlender+'.time')
    pm.connectAttr(mainSpectralWave+'.blender', bossBlender+'.solvers', nextAvailable=True)
    pm.connectAttr(subSpectralWave+'.blender', bossBlender+'.solvers', nextAvailable=True)
    pm.connectAttr(mainSpectralWave+'.outWave', bossBlender+'.inwave', nextAvailable=True)
    pm.connectAttr(subSpectralWave+'.outWave', bossBlender+'.inwave', nextAvailable=True)

    pm.connectAttr(hiFiOceanShape+'.pm', mainSpectralWave+'.parentMatrix')
    pm.connectAttr(hiFiOceanShape+'.bb', mainSpectralWave+'.boundingBox')
    pm.connectAttr(":time1.o", mainSpectralWave+'.time')
    pm.connectAttr(hiFiOceanShape+'.pm', subSpectralWave+'.parentMatrix')
    pm.connectAttr(hiFiOceanShape+'.bb', subSpectralWave+'.boundingBox')
    pm.connectAttr(":time1.o", subSpectralWave+'.time')

    # Cache BOSS output
    solvers = [pm.PyNode(mainSpectralWave), pm.PyNode(subSpectralWave)]
    createBossCache(solvers, 0)

    pm.setAttr(bossTransform+'.visibility', False)

    def postCaching():
        # Set up Arnold skydome
        print 'main cahce: ' + mainWaveCache
        print 'sub cache: ' + subWaveCache
        print 'foam cache: ' + foamCache

        domeLightShape, domeLightNode = mtoa.utils.createLocator("aiSkyDomeLight", asLight=True)
        background = createFileTexture(backgroundFile, 'oceanBackground', 'place2dTexture#')
        pm.connectAttr(background+'.oc', domeLightShape+'.sc')

        # Set up Arnold shader
        waterShader = mtoa.core.createArnoldNode('aiStandardSurface')
        waterShadingEngine = pm.listConnections(waterShader+'.outColor', d=True, s=False)[0]
        setWaterShaderAttributes(waterShader)


        # Create new plane
        projectionOceanTransform, projectionOceanNode = pm.polyPlane(name='projectionOcean', 
                                                                    height=oceanHeight, 
                                                                    width=oceanWidth, 
                                                                    axis=[0,1,0], 
                                                                    subdivisionsWidth=10, 
                                                                    subdivisionsHeight=10)
        projectionOceanShape = pm.listRelatives(projectionOceanTransform, children=True, type='mesh')[0]

        pm.select(projectionOceanShape, replace=True)
        pm.hyperShade(assign=waterShader)

        # Create displacement shader node
        displacementShader = pm.shadingNode('displacementShader', asShader=True)
        pm.connectAttr(displacementShader+'.displacement', waterShadingEngine+'.displacementShader')

        # Create main projection map
        mainWaveDisplacementFile = createFileTexture(mainWaveCache, 'mainWaveDisplacement', 'place2dTexture#')
        pm.setAttr(mainWaveDisplacementFile+'.ufe', True)

        mainWave3dTex = pm.shadingNode('place3dTexture', name='place3dTexture#', asUtility=True)
        mainWaveProjection = pm.shadingNode('projection', name='projection#', asUtility=True)

        pm.rotate(mainWave3dTex, [-90, 0, 0])
        pm.scale(mainWave3dTex, [65, 65, 65])

        pm.connectAttr(mainWaveDisplacementFile+'.oc', mainWaveProjection+'.image')
        pm.connectAttr(mainWave3dTex+'.wim', mainWaveProjection+'.pm')

        # Create sub projection map
        subWaveDisplacementFile = createFileTexture(subWaveCache, 'subWaveDisplacement', 'place2dTexture#')
        pm.setAttr(subWaveDisplacementFile+'.ufe', True)

        subWave3dTex = pm.shadingNode('place3dTexture', name='place3dTexture#', asUtility=True)
        subWaveProjection = pm.shadingNode('projection', name='projection#', asUtility=True)

        pm.rotate(subWave3dTex, [-90, 0, 0])
        pm.scale(subWave3dTex, [35, 35, 35])

        pm.connectAttr(subWaveDisplacementFile+'.oc', subWaveProjection+'.image')
        pm.connectAttr(subWave3dTex+'.wim', subWaveProjection+'.pm')

        # Create color math node
        colorMath = pm.shadingNode('colorMath', name='colorMath#', asUtility=True)
        pm.connectAttr(mainWaveProjection+'.oc', colorMath+'._ca')
        pm.connectAttr(subWaveProjection+'.oc', colorMath+'._cb')
        pm.connectAttr(colorMath+'.oc', displacementShader+'.vectorDisplacement')

        # Create foam projection map
        foamDisplacementFile = createFileTexture(foamCache, 'foamDisplacement', 'place2dTexture#')
        pm.setAttr(foamDisplacementFile+'.ufe', True)

        foam3dTex = pm.shadingNode('place3dTexture', name='place3dTexture#', asUtility=True)
        foamProjection = pm.shadingNode('projection', name='projection#', asUtility=True)

        pm.rotate(foam3dTex, [-90, 0, 0])
        pm.scale(foam3dTex, [30, 30, 30])

        pm.connectAttr(foamDisplacementFile+'.oc', foamProjection+'.image')
        pm.connectAttr(foam3dTex+'.wim', foamProjection+'.pm')

        pm.connectAttr(foamProjection+'.oa', waterShader+'.emission')

        # Set Arnold iteration count
        pm.setAttr(projectionOceanShape+'.aiSubdivType', 2)
        pm.setAttr(projectionOceanShape+'.aiSubdivIterations', numSubDiv)

    # Query for cache output
    queryCache = 'QueryCache'
    if ( pm.window ( queryCache, exists = True ) ):
        pm.deleteUI ( queryCache, window = True )

    global mainWaveCache
    global subWaveCache
    global foamCache
    pm.window ( queryCache, title = "Select cache files", sizeable = True, resizeToFitChildren = True)
    def selectMainWave(*args, **kwargs):
        global mainWaveCache
        mainWaveCache = pm.fileDialog2(dialogStyle=2, fileMode=1)[0]

    def selectSubWave(*args, **kwargs):
        global subWaveCache
        subWaveCache = pm.fileDialog2(dialogStyle=2, fileMode=1)[0]

    def selectFoam(*args, **kwargs):
        global foamCache
        foamCache = pm.fileDialog2(dialogStyle=2, fileMode=1)[0]

    pm.rowColumnLayout(numberOfColumns=2)
    pm.text(label='Main wave cache file')
    pm.button(label='Select file', command=selectMainWave)
    pm.text(label='Sub wave cache file')
    pm.button(label='Select file', command=selectSubWave)
    pm.text(label='Foam cache file')
    pm.button(label='Select file', command=selectFoam)

    def accept(*args, **kwargs):
        if ( pm.window ( queryCache, exists = True ) ):
            pm.deleteUI ( queryCache, window = True )
        postCaching()
    pm.button(label='Accept', command=accept)
    pm.showWindow()

def OceanGenerator():
    # Query for ocean size and background image
    queryForSize = "QueryForSize"
    if ( pm.window ( queryForSize, exists = True ) ):
        pm.deleteUI ( queryForSize, window = True )

    global background
    background = 0
    oceanWidth = 0
    oceanHeight = 0
    subDiv = 0
    pm.window ( queryForSize, title = "Generate Hi-Def Ocean", sizeable = True, resizeToFitChildren = True)
    def selectFile(*args, **kwargs):
        global background
        background = pm.fileDialog2(dialogStyle=2, fileMode=1)[0]

    pm.rowColumnLayout(numberOfColumns=2)
    pm.text(label='Height of created ocean')
    heightField = pm.intField(minValue=10, maxValue=5000, value=300)
    pm.text(label='Width of created ocean')
    widthField = pm.intField(minValue=10, maxValue=5000, value=300)
    pm.text(label='Number of Arnold sub divs')
    subDivField = pm.intField(minValue=1, maxValue=20, value=3)
    pm.text(label='Ocean background HDR')
    pm.button(label='Select file', command=selectFile)

    def accept(*args, **kwargs):
        oceanWidth = pm.intField(widthField, q=True, v=True)
        oceanHeight = pm.intField(heightField, q=True, v=True)
        subDiv = pm.intField(subDivField, q=True, v=True)

        if ( pm.window ( queryForSize, exists = True ) ):
            pm.deleteUI ( queryForSize, window = True )
        generateHiDefOcean(oceanHeight, oceanWidth, subDiv, background)
    pm.button(label='Accept', command=accept)
    pm.showWindow()