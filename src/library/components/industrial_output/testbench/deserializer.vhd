--
-- Copyright (c) ARMadeus Project 2009
--
-- simulation component for SN74HC594
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
-- File          : deserializer.vhd
-- Created on    : 05/06/2009
-- Author        : Fabien Marteau <fabien.marteau@armadeus.com>
-- 
--*********************************************************************

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity deserializer is 
---------------------------------------------------------------------------
port 
(
    rclr_n  : in std_logic ;
    rclk    : in std_logic ;
    srclr_n : in std_logic ;
    srclk   : in std_logic ;
    ser     : in std_logic ;
    q       : out std_logic_vector(7 downto 0);
    qh      : out std_logic
);
end entity;


---------------------------------------------------------------------------
Architecture deserializer_1 of deserializer is
---------------------------------------------------------------------------
    component bascule_d
        port (
                 d   : in std_logic ;
                 clk : in std_logic ;
                 r   : in std_logic ;
                 q   : out std_logic;
                 q_n : out std_logic 
             );
    end component bascule_d;

    component bascule_rs
        port (
                 r1  : in std_logic ;
                 r2  : in std_logic ;
                 clk : in std_logic ;
                 s   : in std_logic;
                 q   : out std_logic;
                 q_n : out std_logic 
             );
    end component bascule_rs;
    
    signal qint_n : std_logic_vector(7 downto 0);
    signal qint   : std_logic_vector(7 downto 0);

    signal srclr : std_logic ;
    signal rclr  : std_logic ;

begin

    srclr <= not srclr_n;
    rclr  <= not rclr_n;

    -- bascule d
    bascule_d_connect : bascule_d
    port map (
                d   => ser,
                clk => srclk,
                r   => srclr,
                q   => qint(0),
                q_n => qint_n(0)
    );

    -- generate bascule rs input
    d_g : for j in 1 to 7 generate
        rs_p2 : bascule_rs
        port map (
                     r1  => qint_n(j-1),
                     r2  => srclr,
                     clk => srclk,
                     s   => qint(j-1),
                     q   => qint(j),
                     q_n => qint_n(j)
                     );
    end generate d_g;

    -- generate bascule rs output
    rs_out : for i in 0 to 7 generate
        rs_p : bascule_rs
        port map (
                     r1  => rclr,
                     r2  => qint_n(i),
                     clk => rclk,
                     s   => qint(i),
                     q   => q(i),
                     q_n => open
                     );
    end generate rs_out;
	
end architecture deserializer_1;

