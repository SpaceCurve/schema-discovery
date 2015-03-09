Schema Discovery Tool for SpaceCurve System
===========================================

The Schema Discovery Tool reads JSON data to create a data definition file for SpaceCurve System.

 - **Prerequisite**: Python 2.7
 - **Note:** This program uses recursion.

Parameters
----------

| Parameter & Alternative | Value | Description   |
| -------------  | -------- | -------- |
| <pre>-f, --input_path</pre>  | *inputPathName* | Required. GeoJSON input filename, pathname, or partial path. Wildcards OK when all schemas match.  |
| <pre>-o, --output_path</pre> | *outputPathName* | DDL output filename, pathname, or partial path. If omitted, no DDL is saved. |
| <pre>-c, --schema_name</pre> | *schemaName* | Schema name to use in DDL output. |
| <pre>-t, --table_name</pre>  | *tableName* | Table name to use in DDL output. |
| <pre>-s, --sample_freq</pre> | *sampleFrequency* | Only sample every *n*th record. Default: 1 |
| <pre>-l, --limit</pre>       | *sampleLimit* | Only sample the first *n* records. Default: 100,000,000 |
| <pre>-a, --attribs_to_lower</pre>  |  | Flag. Convert all attributes to lower-case (implies data conversion). |
| <pre>-v, --verbose</pre> | | Flag. Show verbose log of tool activity. |

Usage
-----

Use this tool to analyze existing JSON and GeoJSON data. This tool can create a file in data definition language (DDL) that defines a database schema. You can use the `scctl` tool to import the DDL file into SpaceCurve System. For information about importing a DDL file, see *Creating Databases and Tables* in the SpaceCurve documentation.

This tool infers data types and value distribution statistics about fields in the source data. This information appears in a comment for each data type in the DDL output.

**Choose Data Types**

The DDL file produced by this tool infers data types where it's able. However, you must review this DDL file to confirm it suits your data. This tool inserts the word **Choose** where you can or must choose a precise data type. For example, SpaceCurve System can accept geometry (flat) and geography (globe-based) geospatial data. If this tool cannot determine any data type based on your source data, you will see **<<Choose** in the comment. For these fields, you must choose a data type that will adequately handle your source data values.

**Partion and Index**

Creating a DDL file with correct datatypes is just one step in importing data to SpaceCurve System. Your database also needs partitioning and indexing that reflects the kinds of queries you will make. Find *System Data Management* in the SpaceCurve documentation for guidance about optimizing queries.

JSON Format
-----------

SpaceCurve System uses a data format similar to GeoJSON. You can see the GeoJSON specification at http://geojson.org/. SpaceCurve uses GeoJSON that does not include a FeatureCollection array. Instead, GeoJSON objects appear sequentially, with no FeatureCollection wrapper, and without commas between records. 

This call uses [the jq tool](http://stedolan.github.io/jq/) to convert standard GeoJSON into a format readable by `schema-discovery.py` and SpaceCurve System:

`jq -c '.features[]' standard.json > spacecurve.json`

See the `radar.json` data file included in the SpaceCurve documentation for an example of data in Spacecurve GeoJSON format.

Example
-------

These lines of `bash` script scan a GeoJSON file, create a DDL file, and create a database instance on the **master** node.

<pre>python schema-discovery.py --input_path spacecurve.json --table_name places --output_path places_schema.sql
scctl shell --ddl --instance_name=places --file=places_schema.sql<pre>
