mcbuilder
=========

mcbuilder is a tool for map making, it replaces signs in minecraft worlds
with blocks like tnt, spawners, chests, etc. based on an xml buildscript.

This is work in progress and not really yet usable.

Example
=======

```xml
<?xml version="1.0" ?>
<mcbuilder>
  <signs>
    <sign data="8" facing="0" id="1" name="tnt block" x="285" y="4" z="938"/>
  </signs>
  <blocks>
    <!-- declare to replace all signs with ID #1 with TNT blocks -->
    <block sign="1" blockName="TNT" />
  </blocks>
</mcbuilder>
```

(Planned) Features:
===================

* replace with spawners, chests, blocks, etc.
* replace with entities like villagers etc.
* support for tileentity nbt data
* "point" signs to reference sign locations in command blocks, etc.
* constants to replace in strings
* usable as multipliers for numerical values
* simple include feature to seperate buildfile in multiple xml files
* include external xml files

```xml
<mcbuilder>
  <include src="mixins.xml" /> 
  ...
</mcbuilder>
```

* mixins with parameters

```xml
<mcbuilder>
  <mixin name="TileEntity">
    <Compound>
      <String name="id">%(param[id])</String>
      <Int name="x">%(x)</Int>
      <Int name="y">%(y)</Int>
      <Int name="z">%(z)</Int>
    </Compound>
  </mixin>
  <signs>...</signs>
  <blocks>
    <block id="1" blockName="Sign">
      <TileEntity id="Sign">
        <String name="Text1">Test.</String>
        <String name="Text2"></String>
        <String name="Text3"></String>
        <String name="Text4"></String>
      </TileEntity>
    </block>
  </blocks>
</mcbuilder>
```




