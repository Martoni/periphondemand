--
-- Copyright (c) ARMadeus Project 2009
--
--
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
-- File          : bascule_d.vhd
-- Created on    : 05/06/2009
-- Author        : Fabien Marteau <fabien.marteau@armadeus.com>
--
--*********************************************************************

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity bascule_d is
---------------------------------------------------------------------------
port
(
    d : in std_logic ;
    clk : in std_logic ;
    r : in std_logic ;
    q : out std_logic;
    q_n : out std_logic
);
end entity;


---------------------------------------------------------------------------
Architecture bascule_d_1 of bascule_d is
---------------------------------------------------------------------------

    signal q_s : std_logic ;

begin

    process (clk)
    begin
        if rising_edge(clk) then
            if r = '1' then
                q_s <= '0';
            else
                q_s <= d;
            end if;
        end if;
    end process;

    q  <= q_s;
    q_n <= not q_s;
end architecture bascule_d_1;

