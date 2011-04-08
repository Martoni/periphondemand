---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 13/05/2009
-- File          : serializer.vhd
--
-- Abstract : this component simulate the behavior of sn65
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity serializer is
---------------------------------------------------------------------------
port
(
    -- serial signals
    clk : in std_logic ;
    ce_n: in std_logic ;
    ld_n: in std_logic ;
    sop : out std_logic ;
    sip : in std_logic ;
    -- parallel input
    input : in std_logic_vector( 7 downto 0)
);
end entity;


---------------------------------------------------------------------------
Architecture serializer_1 of serializer is
---------------------------------------------------------------------------
    signal int_register : std_logic_vector( 7 downto 0):= x"00";
begin

    sop <= int_register(7);

    latch : process (clk,ld_n,ce_n)
    begin
        if ld_n = '0' then
            int_register <= input;
        elsif ce_n = '0' and rising_edge(clk) then
            int_register <= int_register(6 downto 0)&sip;
        end if;
    end process latch;

end architecture serializer_1;

