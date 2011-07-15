---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Fabien Marteau
--
-- Creation Date : 05/07/2011
-- File          : logic_and.vhd
--
-- Abstract : simple logic and
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

Entity logic_and is
    generic(
       input_count : integer := 32 
    );
    port
    (
        logic_inputs : in std_logic_vector(input_count - 1 downto 0);
        logic_output: out std_logic
    );
end entity logic_and;

Architecture logic_and_1 of logic_and is
    constant ONE : std_logic_vector(input_count -1 downto 0) := (others => '1');
begin

    logic_output <= '1' when logic_inputs = ONE else '0';

end architecture logic_and_1;

