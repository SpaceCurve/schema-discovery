Schema Discovery Tool for SpaceCurve System
===========================================

The Schema Discovery Tool for the SpaceCurve System reads JSON data
to create a data definition file for SpaceCurve System.

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
| <pre>-s, --sample_freq</pre> | *sampleFrequency* | Only sample every *n*th record. |
| <pre>-l, -limit</pre>        | *sampleLimit* | Only sample the first *n* records. |
| <pre>-a, --attribs_to_lower</pre>  |  | Flag. Convert all attributes to lower-case (implies data conversion). |
| <pre>-v, --verbose</pre> | | Flag. Show verybose log of tool activity. |

Usage
-----

Use this tool to analyze existing JSON and GeoJSON data. This tool can create a file in data definition language (DDL) that defines a database schema. You can use the `scctl` tool to import the DDL file into SpaceCurve System. For information about importing a DDL file, see *Creating Databases and Tables* in the SpaceCurve documentation.

Examples
--------
