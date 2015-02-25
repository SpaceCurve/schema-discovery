#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Reads JSON data to create a data definition file for SpaceCurve System.
#
# for Python 2.7
#
#
# For help:
#
# python schema-discovery.py --help
#
# and visit: https://github.com/SpaceCurve/schema-discovery
#
# @copyright (C) SpaceCurve, Inc. 2012-2015

import os
import sys
import fileinput
import json
from optparse import OptionParser

ImportedConvertToSupportedGeometry = True


def parse_args():
    usage = 'usage: %prog [options]'
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-f',
        '--input_path',
        dest='ifn',
        metavar='<inputPathName>',
        help='GeoJSON input filename, pathname, or partial path. Wildcards OK when all schemas match.'
        )
    parser.add_option(
        '-o',
        '--output_path',
        dest='ofn',
        default='',
        metavar='<outputPathName>',
        help='DDL output filename, pathname, or partial path'
        )
    parser.add_option(
        '-c',
        '--schema_name',
        dest='schema_name',
        metavar='<schemaName>',
        default='schema',
        help='Schema name to use in DDL output'
        )
    parser.add_option(
        '-t',
        '--table_name',
        dest='table_name',
        metavar='<tableName>',
        help='Table name to use in DDL output'
        )
    parser.add_option(
        '-s',
        '--sampler',
        dest='sampler',
        metavar='<sampleFrequency>',
        default=1,
        help='Only sample every nth record'
        )
    parser.add_option(
        '-l',
        '--limit',
        dest='limit',
        metavar='<sampleLimit>',
        default=None,
        help='Only sample the first n records'
        )
    parser.add_option(
        '-a',
        '--attributes_to_lowercase',
        dest='attributes_to_lowercase',
        action='store_true',
        metavar='<convert attributes_to_lowercase>',
        default=False,
        help='Convert all attributes to lower case (implies data conversion)'
        )
    parser.add_option(
        '-v',
        '--verbose',
        dest='verbose',
        action='store_true',
        metavar='<verbose>',
        default=False,
        help='Show verbose log of tool activity'
        )
    (ctx, args) = parser.parse_args()

    return (parser, ctx)


# Type/Value Histograms

class OneLineHisto:

    """OneLineHisto: depending on the data type, this class gives you a snapshot of the data"""

    def __init__(self):
        self.sum = 0
        self.n = 0
        self.dataTypeDict = {}

    def AddDataType(self, dataType):
        if dataType in ['int', 'float']:
            self.dataTypeDict[dataType] = numberHisto(dataType)
        elif dataType in ['str', 'unicode']:
            self.dataTypeDict[dataType] = strHisto(dataType)
        elif dataType == 'NoneType':
            self.dataTypeDict[dataType] = noneHisto(dataType)
        elif dataType == 'bool':
            self.dataTypeDict[dataType] = boolHisto(dataType)
        else:

#        elif dataType == 'geometry':
#            #geometryHisto(attribute_name = "geometry", dataType = 'geometry')
#            self.dataTypeDict[dataType] = geometryHisto()

            raise 'dataType: %s is invalid' % dataType

    def Add(self, dataType, val):

        # print 'adding: %s %s'%(dataType, str(val))

        if not dataType in self.dataTypeDict:
            self.AddDataType(dataType)
        self.dataTypeDict[dataType].Add(val)

    def export(self):
        rStr = ''
        for k in self.dataTypeDict.keys():
            r = ' %s' % self.dataTypeDict[k].export()
            rStr += r
        return rStr


class numberHisto:

    """numberHisto: Characterizes numeric types"""

    def __init__(self, dataType):
        self.dataType = dataType
        self.n = 0
        self.sum = 0.0
        self.max = None
        self.min = None

    def Add(self, val):
        self.n += 1
        val = float(val)
        self.sum += val
        if self.max == None or self.min == None:
            self.max = val
            self.min = val
        if self.max < val:
            self.max = val
        if self.min > val:
            self.min = val

    def export(self):
        if self.dataType == 'int':
            rstr = '[%s n=%i avg=%i min=%i max=%i]' % (self.dataType,
                    self.n, self.sum / self.n, self.min, self.max)
        else:
            rstr = '[%s n=%i avg=%.2f min=%.2f max=%.2f]' \
                % (self.dataType, self.n, self.sum / self.n, self.min,
                   self.max)
        return rstr


class strHisto:

    def __init__(self, dataType):
        self.dataType = dataType
        self.n = 0
        self.sum = 0.0
        self.max = None
        self.min = None

    def Add(self, instr):
        val = len(instr)
        self.n += 1
        self.sum += float(val)
        if self.max == None or self.min == None:
            self.max = val
            self.min = val
        if self.max < val:
            self.max = val
        if self.min > val:
            self.min = val

    def export(self):
        rstr = '[%s n=%i avg_len=%.1f min=%i max=%i]' % (self.dataType,
                self.n, self.sum / self.n, self.min, self.max)
        return rstr


class boolHisto:

    def __init__(self, dataType):
        self.dataType = dataType
        self.n = 0
        self.n_true = 0
        self.n_false = 0

    def Add(self, bval):
        self.n += 1
        if bval == True:
            self.n_true += 1
        elif bval == False:
            self.n_false += 1
        else:
            raise 'Bad Value: %s' % str(bval)

    def export(self):
        rstr = '[%s n=%i T/F:%i/%i]' % (self.dataType, self.n,
                self.n_true, self.n_false)
        return rstr


class noneHisto:

    def __init__(self, dataType):
        self.dataType = dataType
        self.n = 0

    def Add(self, bval):
        self.n += 1

    def export(self):
        rstr = '[%s n=%i]' % (self.dataType, self.n)
        return rstr


def DetermineType(obj):
    """DetermineType: A hacky way to determine the incoming datatypes"""

    t = str(type(obj))
    if 'dict' in t:
        return 'dict'
    if 'list' in t:
        return 'list'
    if 'int' in t:
        return 'int'
    if 'float' in t:
        return 'float'
    if 'str' in t:
        return 'str'
    if 'NoneType' in t:
        return 'NoneType'
    if 'bool' in t:
        return 'bool'
    try:
        s = str(obj).encode('utf-8')
        return 'unicode'
    except:
        return 'string:Non-unicode'  # unicode(str(obj).content.strip(codecs.BOM_UTF8), 'utf-8')
    return 'unknownType'


##### Geometry section

def ComputeEdgeArea(a, b):

    # Sum over the edges, (x2-x1)(y2+y1).
    # If the result is positive the curve is clockwise,
    # if it's negative the curve is counter-clockwise.
    # (The result is twice the enclosed area, with a +/- convention.)

    (x1, y1) = a
    (x2, y2) = b
    return (x2 - x1) * (y2 + y1)


def IsCCW(coords=[]):
    """IsCCW: simplified version of CCW algorithm"""

    sumarea = 0.0
    for i in range(0, len(coords) - 1, 1):
        area = ComputeEdgeArea(coords[i], coords[i + 1])
        sumarea += area
    if sumarea > 0:
        return False
    else:
        return True


def NoHeightInLatLong(inLst):
    """NoHeightInLatLong: gets rid of third, unsupported coordinate"""

    # print "inLst %s  fixval: %s"%(str(inLst)[:50], str(inLst[0][:2])[:50])

    oLst = []
    for l in inLst:
        oLst.append(l[:2])
    return oLst


def ToPointLst(geoType, cLst):
    coordLst = []
    if geoType == 'Point':
        return cLst
    if geoType == 'LineString':
        for linestrObj in cLst:
            for p in linestrObj:
                coordLst.append(p)
    elif geoType == 'Polygon':
        for polygonObj in cLst:
            for pLst in polygonObj:
                for p in pLst:
                    coordLst.append(p)
    elif geoType == 'MultiPoint':
        return cLst
    elif geoType in ['Polygon_w_Holes', 'MultiPolygon',
                     'MultiPolygon_w_Holes']:
        for c in cLst:
            coordLst.extend(ToPointLst('Polygon', [c]))
    elif geoType == 'MultiLineString':
        for c in cLst:
            coordLst.extend(c)
    else:
        print 'ToPointLst:Unknown Format: %s' % geoType
        return cLst
    return coordLst


def CharacterizeGeometry(gg):
    geo_maxlen = 0
    gtype = gg['type']
    g_coords = gg['coordinates']
    if gtype == 'Point':
        g_coords = g_coords[:2]
        geo_maxlen = 1
        return (gtype, geo_maxlen, [g_coords], [])
    elif gtype == 'LineString':
        geo_maxlen = len(g_coords)
        g_coords = NoHeightInLatLong(g_coords)
        return (gtype, geo_maxlen, [g_coords], [])
    elif gtype == u'Polygon':
        if len(g_coords) > 1:
            pLst = []
            holeLst = []
            geo_maxlen = 0
            for i in range(len(g_coords)):
                c = g_coords[i]
                c = NoHeightInLatLong(c)
                if len(c) > geo_maxlen:
                    geo_maxlen = len(c)
                hole = not IsCCW(coords=c)
                if hole:
                    holeLst.append([c])
                else:
                    pLst.append([c])
                print 'Polygon: part %i has %i points: Hole: %s' % (i,
                        len(c), hole)

            return ('Polygon_w_Holes', geo_maxlen, pLst, holeLst)
        else:
            return ('Polygon', len(g_coords[0]), [g_coords], [])
    elif gtype == 'MultiPoint':
        for pt in g_coords:
            pt = pt[:2]
            if len(pt) > geo_maxlen:
                geo_maxlen = len(pt)
        return (gtype, geo_maxlen, g_coords, [])
    elif gtype == 'MultiLineString':
        out_coords = []
        for ls in g_coords:
            if len(ls) > geo_maxlen:
                geo_maxlen = len(ls)
            out_coords.append(NoHeightInLatLong(ls))
        return (gtype, geo_maxlen, out_coords, [])
    elif gtype == 'MultiPolygon':
        holeLst = []
        pLst = []
        for i in range(len(g_coords)):
            polygon = g_coords[i]
            ret = CharacterizeGeometry({'type': 'Polygon',
                    'coordinates': polygon})
            if 'Holes' in ret[0]:
                gtype = 'MultiPolygon_w_Holes'
                coords = ret[3]
                coords = NoHeightInLatLong(coords)
                holeLst.extend(coords)
            coords = ret[2]
            coords = NoHeightInLatLong(coords)
            pLst.extend(coords)
            lenc = ret[1]
            print 'MultiPolygon: part %i is %s has %i points' % (i,
                    gtype, lenc)
            if lenc > geo_maxlen:
                geo_maxlen = lenc
        return (gtype, geo_maxlen, pLst, holeLst)
    else:
        sys.stderr.write('Unsupported geoJSON type: %s\n'
                         % str(gg))
        return ('GeoNotRecognized: >%s<' % gtype, 0, [], [])


class geometryHisto:

    """geomtryHisto: Inherits a few of the functions of value histograms"""

    # geometryHisto(attribute_name = "geometry", dataType = 'geometry')

    def __init__(self, attribute_name='geometry', dataType='geometry'):
        self.path = 'geometry'
        self.attribute_name = attribute_name
        self.dataType = dataType
        self.GeotypeDict = {}
        self.n = 0
        self.num_coords = 0
        self.parent_n = 0
        self.max = None
        self.min = None
        self.Holes = 0
        self.Nullable = False
        self.Lo_max = None
        self.Lo_min = None
        self.La_max = None
        self.La_min = None

    def ListAllNodes(self):
        return []

    def addCoords(self, geoType, geoObjLst):
        cLst = ToPointLst(geoType, geoObjLst)
        for c in cLst:

            # print 'c: ', c

            try:
                Lo = float(c[0])
                La = float(c[1])
            except:
                print 'Bad Coordinates sent to addCoords: ', c, cLst
                return None
            self.num_coords += 1

            # if Lo == 0.0 or La == 0.0: return None

            if self.Lo_max == None or self.Lo_min == None \
                or self.La_max == None or self.La_min == None:
                self.Lo_max = Lo
                self.Lo_min = Lo
                self.La_max = La
                self.La_min = La
            if self.Lo_max < Lo:
                self.Lo_max = Lo
            if self.Lo_min > Lo:
                self.Lo_min = Lo
            if self.La_max < La:
                self.La_max = La
            if self.La_min > La:
                self.La_min = La

    def BoundBox(self):
        if self.num_coords == 0:
            return '[No BoundingBox Calculated]'

        # print self.num_coords, self.Lo_min, self.La_min, self.Lo_max, self.La_max

        rStr = 'BoundBox: (c= %i) [[%0.4f, %0.4f],[%0.4f, %0.4f]]' \
            % (self.num_coords, self.Lo_min, self.La_min, self.Lo_max,
               self.La_max)
        return rStr

    def PropagateNumRecs(self, n):
        self.parent_n = n
        if self.parent_n != self.n:
            self.Nullable = True

    def DetermineGeoType(self, gObj):
        ret = CharacterizeGeometry(gObj)  # returns >> gtype, geo_maxlen, pLst, holeLst
        geoType = ret[0]
        self.addCoords(geoType, ret[2])

        return (geoType, ret[1])  # ret[2]

    def add(self, gObj):
        self.n += 1
        (geoType, max_numcoords) = self.DetermineGeoType(gObj)
        if not geoType in self.GeotypeDict:
            self.GeotypeDict[geoType] = 1
        else:
            self.GeotypeDict[geoType] += 1
        val = max_numcoords
        if max_numcoords == None:

            # not able to run ImportedConvertToSupportedGeometry

            max_numcoords = 0
            if geoType == 'Polygon':

                # print str(gObj['coordinates'][0])

                val = len(gObj['coordinates'][0])
            if geoType == 'MultiPolygon':
                for c in gObj['coordinates']:
                    if max_numcoords < len(c[0]):
                        max_numcoords = len(c[0])
                val = max_numcoords
            else:
                val = len(gObj['coordinates'])
        if self.max == None or self.min == None:
            self.max = val
            self.min = val
        if self.max < val:
            self.max = val
        if self.min > val:
            self.min = val

    def GenerateDDL(self, geo_type='geography', DumpLastComma=False):
        g = geo_type
        if DumpLastComma:
            comma = ' '
        else:
            comma = ','
        if self.Nullable:
            v = """"%s" %s%s  NULL, -- Choose geometry/geography""" \
                % (self.attribute_name, geo_type, comma)
        else:
            v = """"%s" %s%s  -- Choose geometry/geography""" \
                % (self.attribute_name, geo_type, comma)
        numspaces = max(0, 70 - len(v) + 4)
        spaceStr = ' ' * numspaces
        rStr = '\t%s%s--%s' % (v, spaceStr, self.export())
        return rStr

    def GenerateDDL_VarLine(self, x='', DumpLastComma=False):
        return self.GenerateDDL(DumpLastComma=DumpLastComma)

    def export(self):
        tstr = ''
        for k in self.GeotypeDict.keys():
            tstr = tstr + '%s: %i ' % (k, self.GeotypeDict[k])
        rstr = \
            '[%s n=%i %s points: (min=%i max=%i)] numPolygonsWithHoles: %i // %s' \
            % (
            self.dataType,
            self.n,
            tstr,
            self.min,
            self.max,
            self.Holes,
            self.BoundBox(),
            )
        return rstr


class DataNode:

    """DataNode: Hierarchical data structure element"""

    def __init__(self, key, parent=None):
        if not parent:
            parent_path = 'root'
        else:
            parent_path = parent.path
        self.path = '%s.%s' % (parent_path, key)
        self.ListDictDesc = ''
        self.key = unicode(key)
        self.d = {}
        self.n = 1
        self.parent_n = 1
        self.typeLst = []  # These are types that populate this node
        self.typeLst_ListSupport = []  # Types found inside Lists
        self.DictLst_ListSupport = []  # Dicts found in Lists
        self.histo = None
        self.root_name = ''
        self.Nullable = False
        self.firstValue = None

    def PropagateNumRecs(self, n=None):
        if n == None:
            n = self.n
        self.parent_n = n
        if self.parent_n != self.n:
            print '%s set by Propagation parent_n %i n %i' % (self,
                    self.parent_n, self.n)
            self.Nullable = True
        if 'NoneType' in self.typeLst:
            print '%s set by Propagation NoneType in typeLst: %s' \
                % (self, str(self.typeLst))
            self.Nullable = True
        for k in self.d.keys():
            self.d[k].PropagateNumRecs(n)

    def ListAllNodes(self):
        oLst = [self]
        for k in self.d.keys():

            # if k == 'geometry': continue

            print self.d[k].path
            oLst.extend(self.d[k].ListAllNodes())
        return oLst

    def add(self, key, dictorobj):

        # Three disinct things are done here:
        # 1. add appropriate data histograms to keep track of and characterize built_in types...
        #        like ['int', 'float', 'str', 'unicode', 'NoneType', 'bool', 'geometry']
        # 2. Hold child nodes for embedded types
        # 3. Deal with unusual geometry where a builtin looks on the surface like a dictionary

        key = unicode(key)

        # Seen this key before?

        if key in self.d.keys():

            # pre-existing types

            if key == 'geometry' or self.DetermineType(dictorobj) == 'geometry':

                try:
                    self.d[key].add(dictorobj)
                    return None
                except:

                    # scalar histograms have a different interface for the add function

                    print '''Tried to load this:
 %s 

 Into this: %s''' \
                        % (str(dictorobj), str(self.d[key]))
                    print 'This attribute probably has a mixture of geometry and multiple other types. Unsupported.'
                    sys.exit(0)
            else:
                try:
                    self.d[key].incr()  # just keeps track of the fact that some value existed for this record
                except:
                    print '''Tried to load this:
 %s 

 Into this: %s''' \
                        % (str(dictorobj), str(self.d[key]))
                    print 'This attribute probably has a mixture of geometry and multiple other types. Unsupported.'
                    sys.exit(0)
        else:

            # initialize new types

            if key == 'geometry' or self.DetermineType(dictorobj) == 'geometry':

                # geometryHisto(attribute_name = "geometry", dataType = 'geometry')

                self.d[key] = geometryHisto(attribute_name=key)
                self.d[key].histo = self.d[key]  # weird for geometry types: dict that MUST not spawn a node because it is a builtin This breaks our typing model
                self.d[key].add(dictorobj)
                return None
            else:
                self.d[key] = DataNode(key, self)  # Here you spawn a node

        # Add Type to TypeLst

        dataType = self.addKeyType(key, dictorobj)

        # DataHistogram

        if dataType in [
            'int',
            'float',
            'str',
            'unicode',
            'NoneType',
            'bool',
            ]:
            if self.d[key].histo == None:
                self.d[key].histo = OneLineHisto()
            self.d[key].histo.Add(dataType, dictorobj)
        if dataType == 'NoneType':
            self.Nullabe = True
        if self.d[key].firstValue == None:
            self.d[key].firstValue = dictorobj

    def addKeyType(self, key, dictorobj):
        type_name = self.DetermineType(dictorobj)
        if type_name == 'geometry':
            self.d[key].addType(dictorobj)
        elif type_name == 'dict':
            self.d[key].addType(dictorobj)
            for inkey in dictorobj.keys():
                self.d[key].add(inkey, dictorobj[inkey])
        elif type_name == 'list':

            # ListSupport

            self.d[key].addType(dictorobj)
            self.AddToLst_ListSupport(dictorobj)
        else:
            self.d[key].addType(dictorobj)
        return type_name

    def addType(self, dictorobj):
        type_name = self.DetermineType(dictorobj)
        if not type_name in self.typeLst:
            self.typeLst.append(type_name)

    def AddToLst_ListSupport(self, inLst):
        for elem in inLst:
            t = self.DetermineType(elem)
            if t == 'dict':
                found = False
                for node in self.DictLst_ListSupport:
                    if node.HasKeys(elem):
                        found = True
                        break
                if not found:
                    node = DataNode('Dict_LstElem', self)
                    self.DictLst_ListSupport.append(node)
                node.AddDict(elem)

    def HasKeys(self, indict):
        kscore = 0
        selfkLst = self.d.keys()
        dkLst = indict.keys()
        if len(selfkLst) == len(dkLst):
            for k in dkLst:
                if k in selfkLst:
                    kscore += 1
            if len(selfkLst) == kscore:
                return True
        return False

    def AddDict(self, indict):
        for k in indict.keys():
            self.add(k, indict[k])

    def incr(self):
        self.n += 1

    def DetermineType(self, obj):
        t = str(type(obj))
        if 'dict' in t:
            if self.IsGeometryType(obj):
                return 'geometry'
            return 'dict'
        if 'list' in t:
            return 'list'
        if 'int' in t:
            return 'int'
        if 'float' in t:
            return 'float'
        if 'str' in t:
            return 'str'
        if 'NoneType' in t:
            return 'NoneType'
        if 'bool' in t:
            return 'bool'
        try:
            s = str(obj).encode('utf-8')
            return 'unicode'
        except:
            return 'string:Non-unicode'  # unicode(str(obj).content.strip(codecs.BOM_UTF8), 'utf-8')
        return 'unknownType'

    def IsGeometryType(self, dict_obj):
        if len(dict_obj) == 2:
            if 'type' in dict_obj:
                if 'coordinates' in dict_obj:

                    # print 'GeometryType: ' + str(dict_obj)[:100]

                    return True
        return False

    def DetermineTypeLst_ListSupport(self, inLst):
        tLst = []
        for obj in inLst:
            t = self.DetermineType(obj)
            if not t in tLst:
                tLst.append(t)
        return tLst

    # ### DDL section

    def GenerateDDL(
        self,
        schemaName,
        tableName,
        CleanUpInput=False,
        ):
        """GenerateDDL: This fires off the DDL generation after sufficient data has been loaded"""

        # to be run from root node of data tree

        nLst = self.ListAllNodes()

        # Find outer Node

        node_index = None
        for n in range(len(nLst)):

            # root : ['dict'] : n= 64   path:{root.root.root}

            node = nLst[n]
            if len(node.typeLst) == 1 \
                and node.Generate_DDL_TableTypeOrScalar() == 'type':
                outerNode = node
                node_index = n
                break
        if node_index == None:
            print 'could not find outer node'
            node_index = 1

            # outerNode = nLst[node_index]

            return '[Could not find outer node. check input type. Outer type MUST be dict.]'

        # Tell all the child nodes how many records have been processed by the system
        # Discrepancies here mean that an attribute may need to be made nullable

        outerNode.PropagateNumRecs()

        # Feature type

        oStr = \
            """CREATE TYPE %s.feature IS WHEN "Feature" THEN UNIT;\n""" \
            % schemaName

        # start making attribute types from the parent node onwards

        for n in range(node_index + 1, len(nLst), 1):
            node = nLst[n]
            if node.Generate_DDL_TableTypeOrScalar() == 'type':
                typStr = node.GenerateDDL_CreateType(schemaName,
                        tableName)
                oStr = oStr + '\n' + typStr
                if CleanUpInput:
                    submitStr = self.MakeSubmittableTable(typStr)
                    oStr = oStr + '''

''' + submitStr
            elif node.Generate_DDL_TableTypeOrScalar() == 'geometry':
                geoStr = self.ReturnGeometryType().GenerateDDL()
                oStr = oStr + '\n' + geoStr
                if CleanUpInput:
                    submitStr = self.MakeSubmittableTable(geoStr)
                    oStr = oStr + '''

''' + submitStr
            else:
                pass  # oStr = oStr + '\n--[%s] Unsuported type: %s\n'%(node.path, str(node.typeLst))

        # Make outerNode Table

        ddl_str = outerNode.GenerateDDL_CreateTable(schemaName, tableName)
        oStr = oStr + '\n' + ddl_str
        if CleanUpInput:
            submitStr = self.MakeSubmittableTable(ddl_str)
            oStr = oStr + '\n' + submitStr
        return oStr

    def ReturnGeometryType(self):
        if 'geometry' in self.d:
            return self.d['geometry']
        for k in self.d:
            if isinstance(self.d[k], geometryHisto):
                return self.d[k]
        return None

    def GenerateDDL_VarLine(self, schemaName='', DumpLastComma=False):
        (ddlvar_line, varChoiceString) = self.DDL_VarType(schemaName)
        if AttributesToLower_Case:
            keyname = self.key.lower()
        else:
            keyname = self.key
        numspaces = max(0, 70 - (len(self.key) + len(varChoiceString)
                        + len(ddlvar_line)))
        if DumpLastComma:  # gets rid of trailing commas
            varline_str = '\t"%s" %s %s%s--%s' % (keyname, ddlvar_line,
                    varChoiceString, ' ' * numspaces, self.export())
        else:
            varline_str = '\t"%s" %s,%s%s--%s' % (keyname, ddlvar_line,
                    varChoiceString, ' ' * numspaces, self.export())
        if ddlvar_line == 'NULL':
            return ''  # --' + varline_str
        return varline_str

    def DDL_TableName(self, schemaName, tableName):
        if self.key == 'properties':
            return '%s.%s_%s' % (schemaName, tableName, self.key)
        return '%s.%s' % (schemaName, self.key)

    def DDL_VarType(self, schemaName):
        oLst = []
        used_varchar = False
        self.typeLst.sort()

        # print 'DDL_VarType:%s  %s %s' %(self, self.key, self.firstValue)

        if self.key == 'type' and self.firstValue == 'Feature':
            return ("""%s.feature""" % schemaName, '')
        oStr = ''
        commentStr = ''
        for varType in self.typeLst:
            oStr = ''
            if varType == 'dict':
                if self.key[-3:] == '_ts':
                    oStr = '%s.ts' % schemaName
                else:
                    oStr = self.DDL_TableName(schemaName, table_name)
                    oLst.append(oStr)
                    continue
            if varType == 'list':
                oStr = ' VARRAY of UNSIGNED SMALLINT NULL'
                commentStr += '--Limited ListSupport'
                oLst.append(oStr)
                continue
            if varType in ['str', 'unicode', 'string:Non-unicode']:
                if not used_varchar:
                    oStr = 'VARCHAR'
                    used_varchar = True
                else:
                    continue
            if varType == 'float':
                if self.histo.dataTypeDict[varType].max > 1e38:  # IEEE-754 floating point values:
                    oStr = 'BINARY DOUBLE'
                else:
                    oStr = 'BINARY FLOAT'
            if varType == 'int':
                if self.histo.dataTypeDict[varType].min >= 0:
                    oStr = 'UNSIGNED BIGINT'
                else:
                    oStr = 'BIGINT'
            if self.histo and 'bool' in self.histo.dataTypeDict:
                oStr = ' BOOLEAN'

            # if self.histo and 'NoneType' in self.histo.dataTypeDict:

            if self.Nullable:
                oStr = oStr + ' NULL'
            if varType == 'NoneType':
                continue
            oLst.append(oStr)
        if len(oLst) == 1:
            return (oLst[0], commentStr)
        if len(oLst) == 0:
            return ('NULL', '--[No Values detected In Sample] <<Choose')
        ostr = '|'.join(oLst)
        return (oLst[0], '--[%s] <<Choose' % ostr)

    def GenerateDDL_CreateType(self, schemaName, table_name):
        print 'CreateType %s dict: [n=%i]' \
            % (self.DDL_TableName(schemaName, table_name), len(self.d))
        if self.Generate_DDL_TableTypeOrScalar() == 'type':
            Lst = ['CREATE TYPE %s AS RECORD ('
                   % self.DDL_TableName(schemaName, table_name)]
            keyLst = self.d.keys()

            if keyLst:
                keyLst.sort()
                dumpLastComma = False
                lastKey = keyLst[-1]
                for k in keyLst:
                    if k == lastKey:
                        dumpLastComma = True

                    # Here is where you test for multiple types

                    ddl_varline = \
                        self.d[k].GenerateDDL_VarLine(schemaName,
                            DumpLastComma=dumpLastComma)
                    if ddl_varline:
                        Lst.append(ddl_varline)
            Lst.append(');')
            Rstr = '\n'.join(Lst)
            return Rstr

        # elif self.d:

        return '-- No Type Generation for Leaf Data Node: %s Types: %s' \
            % (self, str(self.typeLst))

    def MakeSubmittableTable(self, inStr):

        # this is only relevant if the ddl processor doe not accept comments correctly.
        # IT strips away the comments and makes a single line entry.

        inLst = inStr.split('\n')
        oLst = []
        for l in inLst:
            l = l.split('--')[0].strip()
            oLst.append(l)
        return '\n' + ''.join(oLst) + '\n'

    def Generate_DDL_TableTypeOrScalar(self):
        if 'geometry' in self.typeLst:
            return 'geometry'
        if 'dict' in self.typeLst:
            return 'type'
        if 'list' in self.typeLst:
            return 'list'
        if self.histo:
            return 'scalar'

    def GenerateDDL_CreateTable(self, schemaName, tableName):
        if self.Generate_DDL_TableTypeOrScalar() == 'type':
            Lst = ['CREATE TABLE %s.%s (' % (schemaName, tableName)]
            keyLst = self.d.keys()
            keyLst.sort()
            lastKey = keyLst[-1]
            dumpLastComma = False
            for k in keyLst:
                if k == lastKey:
                    dumpLastComma = True
                v = self.d[k].GenerateDDL_VarLine(schemaName,
                        DumpLastComma=dumpLastComma)
                if v:
                    Lst.append(v)
            Lst.append(', PARTITION KEY ("geometry")')
            Lst.append(');')
            Rstr = '\n'.join(Lst)
            return Rstr

    # ## EXPORT

    def __str__(self):
        if self.histo:
            histoOutput = self.histo.export()
        else:
            histoOutput = ''
        selfStr = 'DataNode: %s : %s : n= %i%s  %s path:{%s}' % (
            self.key,
            self.typeLst,
            self.n,
            self.ListDictDesc,
            histoOutput,
            self.path,
            )
        return selfStr

    def export(self):
        return str(self)


MaxNumRecsToCount = 100000000
DDL_CleanUpInput = False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.argv.append('--help')

    (parser, ctx) = parse_args()
    Verbose = ctx.verbose
    inpath = ctx.ifn
    if not inpath:
        FileLst = parser.largs
    else:
        FileLst = [inpath]
    AttributesToLower_Case = ctx.attributes_to_lowercase
    table_name = ctx.table_name
    if ctx.limit:
        maxrecsperfile = int(ctx.limit)
    else:
        maxrecsperfile = None
    sampler = int(ctx.sampler)
    schema_name = ctx.schema_name
    ddl_out_path = ctx.ofn
    if not ddl_out_path:
        outUD = os.path.dirname(FileLst[0])
        ddl_out_path = os.path.join(outUD, 'ddl_%s.sql' % table_name)

    root = 'root'
    numf = len(FileLst)
    n = 0
    f = 0
    n_f = 0
    RootNode = DataNode(root)
    for inpath in FileLst:
        n_f = 0
        f += 1
        print inpath
        ifn = os.path.basename(inpath)
        infp = fileinput.input(inpath)
        l = 0
        for line in infp:
            n_f += 1
            l += 1
            if l % 1000 == 0:
                print 'Files %s %i of %i total records processed %i ' \
                    % (ifn, f, numf, n)

                # print line
            # print "%imod%i %i"%(l, sampler, l%sampler)

            if l % sampler > 0:
                continue
            if n > MaxNumRecsToCount:
                break
            if line == '\lf':
                continue
            try:

                # print '>>%s<<'%line[-2:]

                line = line.replace(',  ]', ']')
                if line[-2:] == ',\n':
                    line = line[:-2]
                jsonObj = json.loads(line)
            except:
                print '''Failed Reading this line %i of %i in %s:
>>%s<<
''' \
                    % (l, n, ifn, line)
                continue
            if maxrecsperfile and n_f > maxrecsperfile:
                break
            n += 1
            RootNode.add(table_name, jsonObj)
        infp.close()

    testOut = RootNode.export()
    FileLst_str = '\n'.join([fn for fn in FileLst])
    testOut = FileLst_str + '\n' + testOut
    ddlStr = RootNode.GenerateDDL(schema_name, table_name,
                                  CleanUpInput=DDL_CleanUpInput)
    print ddlStr

    print ddl_out_path
    fp = open(ddl_out_path, 'w')
    fp.write(ddlStr)
    fp.close()

