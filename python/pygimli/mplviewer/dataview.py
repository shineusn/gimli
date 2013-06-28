# -*- coding: utf-8 -*-

import pygimli as g
import pygimli.utils

import pybert as b

from numpy import arange, ndarray, array, ma
import matplotlib as mpl

from colorbar import *

class Pseudotype:
    unknown=0
    A_M=1
    AB_MN=2
    AB_M=3
    AB_N=4
    DipoleDipole=5
    Schlumberger=6
    WennerAlpha=7
    WennerBeta=8
    Gradient=9
    PoleDipole=10
    HalfWenner=11
    Test=99
    
class DataShemeManager():
    '''
    '''
    def __init__( self ):
        '''
        '''
        self.shemes_ = dict()
        self.addSheme( DataShemeBase() )
        self.addSheme( DataShemeWennerAlpha() )
        self.addSheme( DataShemeWennerBeta() )
        self.addSheme( DataShemeDipoleDipole() )
        self.addSheme( DataShemeSchlumberger() )
        self.addSheme( DataShemePoleDipole( ) )
        self.addSheme( DataShemeHalfWenner( ) )

    def addSheme( self, sheme ):
        '''
        '''
        self.shemes_[ sheme.name ] = sheme

    def sheme( self, name ):
        '''
        '''
        if type( name ) == int :
            for s in self.shemes_.values():
                if s.typ == name:
                    return self.shemes_[ s.name ]
            name = 'unknown'

        return self.shemes_[ name ]

    def shemes( self ):
        '''
        '''
        return self.shemes_.keys()
        
class DataShemeBase():
    '''
    '''
    def __init__( self ):
        self.name = "unknown"
        self.prefix = "uk"
        self.typ = Pseudotype.unknown
        self.data_ = None
        self.inverse_ = False
        self.nElectrodes_ = 0
        self.maxSeparation = 1e99
        
    def createElectrodes( self, nElectrodes = 24, electrodeSpacing = 1 ):
        self.data_ = b.DataContainerERT()

        for i in range( nElectrodes ):
            self.data_.createSensor( g.RVector3( float( i ) * electrodeSpacing, 0.0 ) )

        self.nElectrodes_ = self.data_.sensorCount()
         
    def setInverse( self, inverse = False ):
        self.inverse_ = inverse
        
    def setMaxSeparation( self, maxSep ):
        if maxSep > 0.0:
            self.maxSeparation = maxSep
        else:
            self.maxSeparation = 1e99
     
    def createDatum_( self, a, b, m, n, count ):
        if a < self.nElectrodes_ and b < self.nElectrodes_ and m < self.nElectrodes_ and n < self.nElectrodes_:
            if self.inverse_:
                self.data_.createFourPointData( count, m, n, a, b );
            else:
                self.data_.createFourPointData( count, a, b, m, n );
            count += 1                            
        return count
        
class DataShemeDipoleDipole( DataShemeBase ):
    '''
    '''
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Dipole Dipole (CC-PP)"
        self.prefix = "dd"
        self.typ = Pseudotype.DipoleDipole
        self.enlargeEverySep = 0

    def increase(self, l):
        self.enlargeEverySep=l

    def create(self, nElectrodes=24, electrodeSpacing=1, 
               closed=False, complete=False):
        '''
        '''
        self.createElectrodes(nElectrodes, electrodeSpacing)

        ### reserve a couple more than necessary
        self.data_.resize( nElectrodes * nElectrodes )

        count = 0

        if closed:
            space = 1
            for i in range(nElectrodes):
                a = i
                b = (a + space)%nElectrodes
                
                for j in range(nElectrodes):
                    m = (j)%nElectrodes
                    n = (m + space)%nElectrodes
                    
                    if not complete:
                        if j <= i: continue
                        
                    if a != m and a != n and b != m and b!= n:
                        #print a, b, m, n
                        count = self.createDatum_( a, b, m, n, count )

        else:
            maxSep = nElectrodes - 2
            maxInj = nElectrodes - 2
        
            if self.maxSeparation < maxSep:
                maxSep = self.maxSeparation
            
            space = 0
        
            for sep in range( 1, maxSep + 1):
            
                if self.enlargeEverySep > 0:
                    if (sep-1)%self.enlargeEverySep == 0:
                        space +=1
                else:
                    space = 1
                
                for i in range( maxInj - sep ):
                    a = i
                    b = (a + space)%nElectrodes
                    m = (b + sep)%nElectrodes
                    n = (m + space)%nElectrodes
                    #print a, b, m, n
                    count = self.createDatum_( a, b, m, n, count )
                    
        self.data_.removeInvalid()
        return self.data_

class DataShemePoleDipole( DataShemeBase ):
    '''
    '''
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Pol Dipole (C-PP)"
        self.prefix = "pd"
        self.typ = Pseudotype.PoleDipole

    def create( self, nElectrodes = 24, electrodeSpacing = 1 ):
        '''
        '''
        self.createElectrodes( nElectrodes, electrodeSpacing )

        ### reserve a couple more than nesseccary
        self.data_.resize( ( nElectrodes ) * ( nElectrodes ) )
        
        count = 0
        enlargeEverySep = 0
        
        b = -1
        for a in range( 0, nElectrodes ):
            
            for m in range( a + 1, nElectrodes -1 ):
                n = m + 1
                
                if m - a > self.maxSeparation:
                    break
                    
                count = self.createDatum_( a, b, m, n, count )
                    
        self.data_.removeInvalid()
        return self.data_

class DataShemeHalfWenner( DataShemeBase ):
    """Pole-Dipole like Wenner Beta with increasing dipole distance"""
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Half Wenner (C-P-P)"
        self.prefix = "hw"
        self.typ = Pseudotype.HalfWenner

    def create( self, nElectrodes = 24, electrodeSpacing = 1 ):
        """"""
        
        self.createElectrodes( nElectrodes, electrodeSpacing )

        ### reserve a couple more than nesseccary
        self.data_.resize( ( nElectrodes ) * ( nElectrodes ) )

        print "create", self.maxSeparation

        count = 0
        space = 0
        enlargeEverySep = 0
        
        b = -1
        for a in range( 0, nElectrodes ):
            inc = 1
            while True:
                m = a - inc
                n = m - inc
                
                if m < 0 or n < 0 or inc > self.maxSeparation:
                    break
                   
                count = self.createDatum_( a, b, m, n, count )
                inc = inc + 1
                
            inc = 1
            while True:
                m = a + inc
                n = m + inc
                
                if m > nElectrodes or n > nElectrodes or inc > self.maxSeparation:
                    break
                   
                count = self.createDatum_( a, b, m, n, count )
                inc = inc + 1
                    
        self.data_.removeInvalid()
        self.data_.sortSensorsIndex( )
        return self.data_

class DataShemeWennerAlpha( DataShemeBase ):
    '''
    '''
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Wenner Alpha (C-P-P-C)"
        self.prefix = "wa"
        self.typ = Pseudotype.WennerAlpha

    def create( self, nElectrodes = 24, electrodeSpacing = 1 ):
        '''
        '''
        self.createElectrodes( nElectrodes, electrodeSpacing )

        maxSep = nElectrodes - 2
        if self.maxSeparation < maxSep:
            maxSep = self.maxSeparation

        ### reserve a couple more than nesseccary
        self.data_.resize( nElectrodes * nElectrodes )

        count = 0

        for sep in range( 1, maxSep + 1):
            for i in range( ( nElectrodes - 2 ) - sep ):
                a = i
                m = a + sep
                n = m + sep
                b = n + sep
                count = self.createDatum_( a, b, m, n, count )

        self.data_.removeInvalid()
        return self.data_

class DataShemeWennerBeta( DataShemeBase ):
    '''
    '''
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Wenner Beta(C-C-P-P)"
        self.prefix = "wb"
        self.typ = Pseudotype.WennerBeta

    def create( self, nElectrodes = 24, electrodeSpacing = 1 ):
        '''
        '''
        self.createElectrodes(  nElectrodes, electrodeSpacing  )

        maxSep = nElectrodes - 2
        if self.maxSeparation < maxSep:
            maxSep = self.maxSeparation

        ### reserve a couple more than nesseccary
        self.data_.resize( ( nElectrodes *nElectrodes ) )

        count = 0

        for sep in range( 1, maxSep + 1):
            for i in range( ( nElectrodes - 2 ) - sep ):
                a = i
                b = a + sep
                m = b + sep
                n = m + sep
                
                count = self.createDatum_( a, b, m, n, count )
                    
        self.data_.removeInvalid()
        return self.data_
# class DataShemeSchlumberger( ... )

class DataShemeSchlumberger( DataShemeBase ):
    '''
    '''
    def __init__( self ):
        DataShemeBase.__init__( self )
        self.name = "Schlumberger(C-PP-C)"
        self.prefix = "slm"
        self.typ = Pseudotype.Schlumberger

    def create( self, nElectrodes = 24, electrodeSpacing = 1  ):
        '''
        '''
        self.createElectrodes(  nElectrodes, electrodeSpacing  )

        maxSep = nElectrodes - 2
        if self.maxSeparation < maxSep:
            maxSep = self.maxSeparation

        self.data_.resize( nElectrodes * nElectrodes )

        count = 0

        for sep in range( 1, maxSep + 1 ):
            for i in range( ( nElectrodes - 2 ) - sep ):
                a = i
                m = a + sep
                n = m + 1
                b = n + sep
                count = self.createDatum_( a, b, m, n, count )
                    
        self.data_.removeInvalid()
        return self.data_
# class DataShemeSchlumberger( ... )










def createPseudoPosition( data, pseudotype = Pseudotype.unknown, scaleX = False ):
    '''
        Create pseudo x position and separation for the dataset
        ScaleX: scales the x positions regarding the real electrode positions
    '''
    nElecs = data.sensorCount()
    
    if pseudotype == Pseudotype.DipoleDipole:
        x = ( data( 'a' ) + data( 'b' ) + data( 'm' ) + data( 'n' ) ) / 4.0;
        sep = g.abs( ( data( 'n' ) + data( 'm' ) ) / 2.0 - ( data( 'b' ) + data( 'a' ) ) / 2.0 )
        
    elif pseudotype == Pseudotype.WennerBeta:
        x = ( data( 'a' ) + data( 'b' ) + data( 'm' ) + data( 'n' ) ) / 4.0;
        sep = g.abs( ( data( 'n' ) + data( 'm' ) ) / 2.0 - ( data( 'b' ) + data( 'a' ) ) / 2.0 ) / 2.0
        sep = sep + 1.

    elif pseudotype == Pseudotype.WennerAlpha:
        x = ( data( 'a' ) + data( 'b' ) + data( 'm' ) + data( 'n' ) ) / 4.0;
        sep = g.abs( ( data( 'b' ) - data( 'a' ) ) / 2.0 + ( data( 'n' ) - data( 'm' ) ) / 2.0 ) / 2.0
        sep = sep + 1.
        
    elif pseudotype == Pseudotype.Schlumberger:
        x = ( data( 'a' ) + data( 'b' ) + data( 'm' ) + data( 'n' ) ) / 4.0;
        sep = g.abs( ( data( 'b' ) - data( 'a' ) ) / 2.0 + ( data( 'n' ) - data( 'm' ) ) / 2.0 )
        
    elif pseudotype == Pseudotype.PoleDipole:
        x = data( 'm' )
        sep = g.abs( data( 'a' ) - data( 'm' ) ) 
        sep = sep + 1.
    
    elif pseudotype == Pseudotype.HalfWenner:
        x = data( 'm' )
        sep = data( 'a' ) - data( 'm' ) 
        sep = sep + 1.
        
    elif pseudotype == Pseudotype.Gradient:
        x = ( data( 'm' ) + data( 'n' ) ) / 2.0;

        def psmin( vec1, vec2 ):
            ret = g.RVector( vec1.size(), 0.0 )
            for i in range( len( vec1 ) ):
                ret[i] = min( vec1[i], vec2[i] )
            return ret
        sep = psmin( ( x - data( 'a' ) ), ( data('b') - x ) ) / 3.0

    elif pseudotype == Pseudotype.AB_MN:
        x = data( 'a' ) * float( nElecs ) + data( 'b' );
        sep = data( 'm' ) * float( nElecs ) + data( 'n' );
    elif pseudotype == Pseudotype.AB_M:
        x = data( 'a' ) * float( nElecs ) + data( 'b' );
        sep = data( 'm' );
    elif pseudotype == Pseudotype.AB_N:
        x = data( 'a' ) * float( nElecs ) + data( 'b' );
        sep = data( 'n' );
    elif pseudotype == Pseudotype.Test:
        x = data( 'a' ) * float( nElecs ) + data( 'b' );
        sep = g.abs( data( 'm' ) - data( 'n' ) ) * float( nElecs )* float( nElecs ) + \
                data( 'm' ) * float( nElecs ) + data( 'n' );
    else:
        x = g.RVector( data( 'a' ) )
        sep = g.RVector( data( 'm' ) )

    ### need a copy here , so we do not change the original data
    x = g.RVector( x )
    sep = g.RVector( sep )

    if scaleX:
        x += data.sensorPositions()[ 0 ][ 0 ]
        x *= data.sensorPositions()[ 0 ].distance( data.sensorPositions()[ 1 ] )
        sep -= 1.
        sep *= -1.
            
    return x, sep
# def createPseudoPosition( ... )

def createDataMatrix( data, values, pseudotype = Pseudotype.unknown ):
    nElecs = data.sensorCount();
    nData  = data.size();

    #create horizontal (separations) and vertical (x)'pseudopositions' for each datapoint
    x, sep = createPseudoPosition( data, pseudotype )

    # unique separations
    Sidx = g.unique( g.sort( sep ) )
    
    # unique x-position
    Xidx = g.unique( g.sort( x ) )
    
    # scale parameter
    dataWidthInMatrix = 1
    xOffset = 0
    xLength = len( Xidx )

    if pseudotype > 2 and len( Xidx ) > 1:
        
        if g.min( g.utils.diff( Xidx ) ) < 1.0:

            dataWidthInMatrix = int( 1.0 / g.min( g.utils.diff( Xidx ) ) )
            if dataWidthInMatrix > 1:    
                xOffset = int( Xidx[0] * dataWidthInMatrix ) -1
                xLength = (nElecs -1)* dataWidthInMatrix

    print "xLength: ", xLength
    
    mat = np.ndarray(shape=(len( Sidx ), xLength,), dtype=float, order='F')

    #mat = arange( 0.0, len( Sidx ) * xLength )
    mat[ : ] = 0.0
    mat = ma.masked_where( mat == 0.0, mat )
    #mat = mat.reshape( len( Sidx ), xLength )

    for i in range( 0, nData ):
        if data.get( 'valid' )[i]:
            mat[ g.find( Sidx == sep[ i ] ), g.find( Xidx == x[ i ] ) + xOffset ] = values[ i ]
        
            for j in range( 1, dataWidthInMatrix ):
                mat[ g.find( Sidx == sep[ i ] ), g.find( Xidx == x[ i ] ) + xOffset + j ] = values[ i ]

            
    print "datasize:", data.size(), "shown: ", len( mat[~mat.mask] ) / dataWidthInMatrix
    notShown = ( data.size() - len( mat[~mat.mask] ) / dataWidthInMatrix )
    
    if notShown > 0:
        print "data not shown: ", notShown
    #print mat
    return mat, Xidx, Sidx, dataWidthInMatrix;
# END def createDataMatrix( ... )

def drawDataAsMatrix( ax, data, values, pseudotype = Pseudotype.unknown, mat = None, logScale = True ):
    """
        Draw data as matrix image in axes ax
    """

    norm = None

    if values is None:
        if mat is not None:
            if isinstance( mat, g.RMatrix ):
                # t = [ ]
                # for i in mat: t.append( g.RVectorToList( i ) )
                # m = array( t )
                # m.reshape( len( mat ), len( mat[ 0 ] ) )
                t = zeros( ( len( mat ), len( mat[ 0 ] ) ) )
                for i, row in enumerate( mat ):
                    t[i] = row
                mat = t
            elif isinstance( mat, list ):
                t = [ ]
                for i in mat: t.append( i )
                m = array( t )
                m.reshape( len( mat ), len( mat[ 0 ] ) )
                mat = m

        else:
            raise Exception, ( 'drawDataAsMatrix(...) No values or matrix given.' )
    else: 
        cmin = g.min( values )
        cmax = g.max( values )

        if cmin <= 0: 
            logScale = False
            
        if logScale:
            values, cmin, cmax = findAndMaskBestClim( values, cMin = None, cMax = None, dropColLimitsPerc = 5 )
            norm = mpl.colors.LogNorm()

    matSpacing = None
    
    if mat is None:
        if data:
            mat, matXidx, matSidx, matSpacing = createDataMatrix( data, values, pseudotype )
        else:
            raise Exception, ( 'no data or matrix given' )

    mat = ma.masked_where( mat == 0.0, mat )

    if min( mat.flat ) < 0:
        norm = mpl.colors.Normalize()
    else:
        norm = mpl.colors.LogNorm()
            
    print mat
            
    image = ax.imshow( mat, interpolation = 'nearest'
                            , norm = norm
                            , lod = True )

    image.get_cmap().set_bad( [1.0, 1.0, 1.0, 0.0 ] )

    print mat.shape
    print min( matXidx ), max( matXidx ), matSidx, matSpacing
    
    # check with co2man data@l.e.
    #ax.set_xlim( data.sensorPositions()[0][0]  - matSpacing, 
                 #data.sensorPositions()[-1][0] + matSpacing )
    
    annotateSeparationAxis( ax, pseudotype, grid = True )

    return image
# END def drawDataAsMatrix( ... )

def annotateSeparationAxis( ax, shemeID, grid = False ):
    '''
        Draw y-axes tick labels corresponding to the separation
    '''
    prefix = DataShemeManager().sheme( shemeID ).prefix
    
    def sepName( l ):
        suffix = ""
        
        if l == 0:
            return ''
        elif l > 0:
            suffix = "'"
                
        if grid:
            ax.plot( ax.get_xlim(), [l,l], color = 'black', linewidth = 1, linestyle='dotted')
        
        return prefix + ' $' + str( abs(int( l )) ) + suffix +'$'

    ax.yaxis.set_ticklabels( map( lambda l: sepName( l ), ax.yaxis.get_ticklocs() ) )
    
# END def annotateSeparations( ... )

def drawElectrodesAsMarker( ax, data ):
    '''
        Draw electrode marker, these marker are pickable
    '''
    elecsX = []
    elecsY = []
    
    for i in range( len( data.sensorPositions() ) ):
        elecsX.append( data.sensorPositions()[i][ 0 ] )
        elecsY.append( data.sensorPositions()[i][ 1 ] )
    
    electrodeMarker, =  ax.plot( elecsX, elecsY, 'x', color = 'black', picker = 5. )
    
    ax.set_xlim( [ data.sensorPositions()[0][0]-1., data.sensorPositions()[ data.sensorCount() -1][0] + 1. ] )
    #print electrodeMarker
    return electrodeMarker
# END def drawElectrodesAsMarker( ... )

def drawDataAsMarker( ax, data, shemetype = Pseudotype.unknown ):
    '''
        Draw pseudosection sheme for the data using marker only
    '''
    
    # first draw the electrodes
    electrodeMarker = drawElectrodesAsMarker( ax, data )
        
    # now draw the data Marker
    x, sep = createPseudoPosition( data, shemetype, scaleX = True  )
    
    maxSepView = max( sep ) + 2
    if max( sep ) > 0: maxSepView = maxSepView - 1
    ax.set_ylim( [ min( sep ) - 1, maxSepView ] )
    
    dataMarker, = ax.plot( x, sep, '.', color='black', picker = 5. )
    
    annotateSeparationAxis( ax, shemetype, grid = True )
    
    return electrodeMarker, dataMarker
# END def drawDataAsMarker( ... )

def createDataPatches( ax, data, shemetype = Pseudotype.unknown, **kwarg ):
    '''
        Create patches to display a pseudosection
    '''
    swatch = g.Stopwatch( True )
    x, sep = createPseudoPosition( data, shemetype, scaleX = True )
    
    ax.set_ylim( [ min( sep )-1, max( sep )+1 ] )

    #dx2 = (data.sensorPositions()[1][0] - data.sensorPositions()[0][0])/4.
    dx2 = (x[1]-x[0])/4.
    dSep2 = 0.5
    
    polys = []
    for i, xv in enumerate( x ):
        s = sep[ i ]
        polys.append( zip( [ xv-dx2, xv+dx2, xv+dx2, xv-dx2],
                               [ s - dSep2, s - dSep2, s + dSep2, s + dSep2 ] ) )

    patches = mpl.collections.PolyCollection( polys, antialiaseds = False, lod = True, **kwarg)
    patches.set_edgecolor( 'face' )
    #patches.set_linewidth( 0.001 )
    ax.add_collection( patches )
    
    print "Create data patches takes t = ", swatch.duration( True )
    return patches
# END def createDataPatches( ... )

def drawDataAsPatches( ax, data, values, shemetype = Pseudotype.unknown, writeValues = False, **kwarg ):
    '''
        Draw pseudosection as patch graphic
    '''
    # first draw the electrodes
    electrodeMarker = drawElectrodesAsMarker( ax, data )

    # now draw the data Marker
    gci = createDataPatches( ax, data, shemetype, **kwarg )
    
    vals = ma.masked_where( values == 0, values * data.get( 'valid') )
        
    g.mplviewer.setMappableData( gci, vals, logScale = True )
    
    #if min( values ) < 0 :
    #    writeValues = True
        
    if writeValues:
        x, sep = createPseudoPosition( data, shemetype, scaleX = True )
        
        for i, xv in enumerate( x ):
            ax.text( xv, sep[i], str( round( values[ i ], 2) )
                       , fontsize='8', horizontalalignment='center', verticalalignment='center'  )
    
    
    annotateSeparationAxis( ax, shemetype, grid = True )
    return gci
# END def drawDataAsPatches( ... )
    
def drawTravelTimeData( a, data ):
    '''
        Draw first arrival traveltime data into mpl axes a. 
        data of type \ref DataContainer must contain sensorIdx 's' and 'g' and thus numbered internal from [0..n)
    '''

    x = g.x( data.sensorPositions() )
    z = g.z( data.sensorPositions() )

    shots = g.unique( g.sort( data('s') ) )
    geoph = g.unique( g.sort( data('g') ) )

    startOffsetIDX = 0

    if min( min( shots ), min( geoph ) == 1 ): 
        startOffsetIDX = 1
    
    a.set_xlim( [ min(x), max(x) ] )
    a.set_ylim( [ max( data('t') ), -0.002 ] )
    a.figure.show()
    
    for shot in shots:
        gIdx = g.find( data('s') == shot )
        sensorIdx = map( lambda i__: int( i__ - startOffsetIDX ), data('g')[ gIdx ] )
        a.plot( x[ sensorIdx ], data('t')[ gIdx ], 'x-')
            
    yPixel = a.transData.inverted().transform_point( (1, 1) )[1]-a.transData.inverted().transform_point( (0, 0) )[1]
    xPixel = a.transData.inverted().transform_point( (1, 1) )[0]-a.transData.inverted().transform_point( (0, 0) )[0]

    # draw shot points
    a.plot( x[ map( lambda i__: int( i__ - startOffsetIDX), shots ) ], np.zeros( len( shots ) ) + 8.*yPixel, 'gv', markersize = 8 )    

    # draw geophone points
    a.plot( x[ map( lambda i__: int( i__ - startOffsetIDX), geoph ) ], np.zeros( len( geoph ) ) + 3.*yPixel, 'r^', markersize = 8 )    

    a.grid( )    
    a.set_ylim( [ max( data('t') ), +16.*yPixel] )
    a.set_xlim( [ min(x)-5.*xPixel, max(x)+5.*xPixel ] )

    a.set_xlabel('x-Coordinate [m]')
    a.set_ylabel('Traveltime [ms]')
# def drawTravelTimeData( ... )