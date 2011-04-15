--
-- Copyright (c) ARMadeus Systems 2010
--
-- This program is free software; you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation; either version 2, or (at your option)
-- any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
--*********************************************************************
--
-- File          : apf51_test_pkg.vhd
-- Created on    : 20/12/2010
-- Author        : Fabien Marteau <fabien.marteau@armadeus.com>
--
--*********************************************************************

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

package apf51_test_pkg is

    CONSTANT CS_MIN : time := 13.6 ns;
    CONSTANT HALF_CLOCK_PERIOD : time := 6 ns;
    CONSTANT WE3 : time := 2.25 ns;
    CONSTANT WE4 : time := 2.25 ns;

    -- write procedures
    -- Params :
    --    address      : Write address
    --    value        : value to write
    --    gls_clk      : clock signal
    --    imx_cs_n     : Chip select
    --    imx_rw       : Read/Write signal
    --    imx_adv      : address/data mux signal
    --    imx_da       : Data/Address signal
    --    WWSC         : Value of imx WWSC

    procedure imx_write(
    address     : in std_logic_vector (15 downto 0);
    signal value       : in std_logic_vector (15 downto 0);
    signal gls_clk     : in std_logic ;
    signal imx_cs_n    : out std_logic ;
    signal imx_rw      : out std_logic ;
    signal imx_adv     : out std_logic ;
    signal imx_da      : inout std_logic_vector (15 downto 0);
    WWSC         : natural
);
    -- read procedures
    -- Params :
    --    address      : Write address
    --    value        : value returned
    --    gls_clk      : clock signal
    --    imx_cs_n     : Chip select
    --    imx_rw       : Read/Write signal
    --    imx_adv      : address/data mux signal
    --    imx_da       : Data/Address signal
    --    RWSC          : Value of imx WSC (see MC9328MXLRM.pdf p169) for sync=0

procedure imx_read(
    address : in std_logic_vector( 15 downto 0);
    signal value   : out std_logic_vector( 15 downto 0);
    signal gls_clk : in std_logic ;
    signal imx_cs_n: out std_logic ;
    signal imx_rw  : out std_logic ;
    signal imx_adv : out std_logic ;
    signal imx_da  : inout std_logic_vector( 15 downto 0) ;
    RWSC  : natural
   );

end package apf51_test_pkg;

package body apf51_test_pkg is

    -- Write value from imx
    procedure imx_write(
    address     : in std_logic_vector (15 downto 0);
    signal value    : in std_logic_vector (15 downto 0);
    signal gls_clk  : in std_logic;
    signal imx_cs_n : out std_logic;
    signal imx_rw   : out std_logic;
    signal imx_adv  : out std_logic;
    signal imx_da   : inout std_logic_vector (15 downto 0);
    WWSC : natural
    ) is
begin
    -- Write value
    wait until rising_edge(gls_clk);
    imx_da <= address(15 downto 0);
    imx_rw <= '0';
    imx_adv <= '0';
    imx_cs_n <= '1';
    wait until rising_edge(gls_clk);
    imx_adv <= '1';
    imx_cs_n <= '0';
    imx_da  <= value;
    if WWSC <= 1 then
        wait until rising_edge(gls_clk);
    else
        for n in 1 to WWSC loop
            wait until rising_edge(gls_clk); -- WWSC > 1
        end loop;
    end if;
    wait for 1 ns;
    imx_cs_n <= '1';
    imx_adv <= '1';
    imx_da  <= (others => 'Z');
end procedure imx_write;

-- Read a value from imx
procedure imx_read(
    address : in std_logic_vector( 15 downto 0);
    signal value   : out std_logic_vector( 15 downto 0);
    signal gls_clk : in std_logic ;
    signal imx_cs_n: out std_logic ;
    signal imx_rw  : out std_logic ;
    signal imx_adv : out std_logic ;
    signal imx_da  : inout std_logic_vector( 15 downto 0 ) ;
    RWSC  : natural
    ) is
begin
    -- Read value
    wait until rising_edge(gls_clk);
    imx_da <= address(15 downto 0);
    imx_cs_n <= '1';
    imx_rw <= '1';
    imx_adv <= '0';
    wait until rising_edge(gls_clk);
    imx_da <= (others => 'Z');
    imx_cs_n <= '0';
    imx_adv <= '1';
    if RWSC > 1 then
        for n in 2 to RWSC loop
            wait until rising_edge(gls_clk);
        end loop;
    end if;
    value <= imx_da;
    imx_cs_n <= '1';
    imx_da <= (others => 'Z');
end procedure imx_read;

end package body apf51_test_pkg;
