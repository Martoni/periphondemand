--
-- Copyright (c) ARMadeus Project 2011
--
-- Drive a SJA1000 CAN controller with Wishbone bus
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
-- File          : sja1000.vhd
-- Created on    : 05/05/2011
-- Author        : Kevin JOLY joly.kevin25@gmail.com
--
--*********************************************************************
library IEEE;
use IEEE.STD_LOGIC_1164.all;

entity sja1000 is
    generic (
                id : natural := 1;
                wb_size : natural := 16
            );
    port (
        -- Syscon signals
             gls_reset       : in std_logic ;
             gls_clk         : in std_logic ;
        -- Wishbone signals
             wbs_add         : in std_logic_vector (7 downto 0);
             wbs_writedata   : in std_logic_vector( wb_size-1 downto 0);
             wbs_readdata    : out std_logic_vector( wb_size-1 downto 0);
             wbs_strobe      : in std_logic ;
             wbs_cycle       : in std_logic ;
             wbs_write       : in std_logic ;
             wbs_ack         : out std_logic;
        --sja signals
             sja_ad          : inout std_logic_vector(7 downto 0);
             sja_ale_as      : out std_logic := '1';
             sja_cs          : out std_logic := '1';
             sja_rd          : out std_logic := '1';
             sja_wr          : out std_logic := '1'
         );
end entity sja1000;

architecture sja1000_drive of sja1000 is
--State signal
    type state_type is (init, address, val_address,start_cs,
                        read_data, end_read, write_data,
                        end_write, end_cs_write, end_cs_read);
    signal state : state_type := init;
    signal data_to_write : std_logic_vector(7 downto 0);
begin

    fsm : process(gls_clk, gls_reset)
    begin

        if gls_reset = '1' then
            --Return to the waiting state
            state       <= init;
        elsif rising_edge(gls_clk) then

            case state is
                when init =>
                    if (wbs_strobe and wbs_cycle) = '1' then
                        state <= address;
                    end if;
                when address =>
                    state <= val_address;
                when val_address =>
                    state <= start_cs;
                when start_cs =>
                    if wbs_write = '1' then
                        state <= write_data;
                    else
                        state <= read_data;
                    end if;
                --Write
                when write_data =>
                    if wbs_strobe = '0' then
                        state <= end_write;
                    else
                        data_to_write <= wbs_writedata(7 downto 0);
                    end if;
                when end_write =>
                    if wbs_strobe = '0' then
                        state <= end_cs_write;
                    end if;
                when end_cs_write =>
                    state <= init;
                --Read
                when read_data =>
                    if wbs_strobe = '0' then
                        state <= end_read;
                    end if;
                when end_read =>
                    state <= end_cs_read;

                when end_cs_read =>
                    state <= init;
            end case;
        end if;
    end process fsm;

    sja_ad  <=  wbs_add when state = address or state = val_address else
                        data_to_write when state = write_data or
                                           state = end_write or
                                           state = end_cs_write else
                                      (others => 'Z');

    sja_ale_as  <=  'H' when state = address    else
                        '0';

    sja_rd  <=  '0' when state = read_data else
                    'H';

    sja_wr  <=  '0' when state = write_data else
                    'H';

    sja_cs  <=  '0' when state = write_data or
                         state = read_data or
                         state = end_read or
                         state = end_write or
                         state = start_cs else
                    '1';

    wbs_readdata(7 downto 0) <= sja_ad when state = end_read or
                                            state = read_data else
                                       (others => '0');

end architecture sja1000_drive;


