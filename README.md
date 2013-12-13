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
        <sign id="1">tnt blocks</sign>
        <sign id="2">pig newton spawner, spawns pig newtons</sign>
        <sign id="3">a chest with some loot</sign>
    </signs>
    <blocks>
        <block blockName="TNT" sign="1" data="0"/>
        <block sign="2" blockName="Spawner">
            <Compound>
                <String name="id">MobSpawner</String>
                <Int name="x">%(x)</Int>
                <Int name="y">%(y)</Int>
                <Int name="z">%(z)</Int>
                <String name="EntityId">Pig</String>
                <Compound name="SpawnData">
                    <String name="CustomName">Pig Newton</String>
                    <Byte name="CustomNameVisible">1</Byte>
                </Compound>
            </Compound>
        </block>
        <block sign="3" blockName="Chest">
            <Compound>
                <String name="id">Chest</String>
                <Int name="x">%(x)</Int>
                <Int name="y">%(y)</Int>
                <Int name="z">%(z)</Int>
                <List name="Items">
                    <Compound>
                        <Byte name="Slot">13</Byte>
                        <Short name="id">278</Short>
                        <Short name="Damage">0</Short>
                        <Byte name="Count">1</Byte>
                        <Compound name="tag">
                            <Compound name="display">
                                <String name="Name">Pick of Destiny</String>
                                <List name="Lore">
                                    <String>I do not need</String>
                                    <String>He does not need</String>
                                    <String>A microphone</String>
                                    <String>A microphone</String>
                                </List>
                            </Compound>
                        </Compound>
                    </Compound>
                </List>
            </Compound>
        </block>
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




