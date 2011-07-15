---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Fabien Marteau
--
-- Creation Date : 05/07/2011
-- File          : logic_or.vhd
--
-- Abstract : simple logic or
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

Entity logic_or is
    generic(
       input_count : integer := 32 
    );
    port
    (
        logic_inputs : in std_logic_vector(input_count - 1 downto 0);
        logic_output: out std_logic
    );
end entity logic_or;

Architecture logic_or_1 of logic_or is
    constant ZERO : std_logic_vector(input_count -1 downto 0) := (others => '0');
begin

    logic_output <= '0' when logic_inputs = ZERO else '1';

end architecture logic_or_1;

