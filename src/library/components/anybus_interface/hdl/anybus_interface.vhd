--
-- Copyright (c) ARMadeus Project 2011
--
-- Interface with the HMS Module ANYBUS
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
-- File          : anybus_interface.vhd
-- Created on    : 12/05/2011
-- Author        : Kevin JOLY joly.kevin25@gmail.com
--
--*********************************************************************
library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

entity anybus_interface is
    generic (
                ID : natural := 1;
                wb_size : natural := 16
            );
    port (
            -- Syscon signals
            gls_reset           : in std_logic;
            gls_clk             : in std_logic;
            -- Wishbone signals
            wbs_add             : in std_logic_vector (1 downto 0);
            wbs_writedata       : in std_logic_vector( wb_size-1 downto 0);
            wbs_readdata        : out std_logic_vector( wb_size-1 downto 0);
            wbs_strobe          : in std_logic;
            wbs_cycle           : in std_logic;
            wbs_write           : in std_logic;
            wbs_ack             : out std_logic;
            --hms anybus signals
            anybus_interface_addr     : out std_logic_vector(11 downto 0);
            anybus_interface_data     : inout std_logic_vector(7 downto 0);
            anybus_interface_busy     : in std_logic;
            anybus_interface_oe       : out std_logic;
            anybus_interface_rw       : out std_logic;
            anybus_interface_ce       : out std_logic
         );
end entity anybus_interface;

architecture anybus_interface_arch of anybus_interface is
    --State signal for anybus
    type state_anybus_type is (init_anybus,start, read, end_read, write, end_write);
    signal state_anybus : state_anybus_type := init_anybus;

    --State signal for Wishbone Bus
    type state_wb_type is (init_wb, read_register, write_register, transmission_error);
    signal state_wb : state_wb_type := init_wb;

    --Registers
    --In the worst case, the interface will wait 7 clock cycles
    signal CONTROL_REG  : std_logic_vector(wb_size-1 downto 0) := x"0000";
    signal ADDRESS_REG  : std_logic_vector(wb_size-1 downto 0) := x"0000";
    signal DATA_READ_REG    : std_logic_vector(wb_size-1 downto 0) := x"0000";
    signal DATA_WRITE_REG   : std_logic_vector(wb_size-1 downto 0) := x"0000";

    --Status signals
    signal communication_error : std_logic := '0';
    signal transmission : std_logic := '0';
    signal reception : std_logic := '0';
    signal com_in_progress : std_logic := '0';
    signal wait_clock_cycles : integer range 0 to 7 := 7;

    --write message signals
    signal message_addr : std_logic_vector(11 downto 0);
    signal message_data : std_logic_vector(7 downto 0);
begin

    --FSM of the Wishbone interface
    fsm_wb_interface : process(gls_clk, gls_reset)
    begin
        if gls_reset = '1' then
            --Return to the waiting state
            state_wb            <= init_wb;
            transmission        <= '0';
            reception           <= '0';
            communication_error <= '0';
            ADDRESS_REG         <= (others => '0');
            DATA_WRITE_REG      <= (others => '0');
            wait_clock_cycles   <= 7;
        elsif rising_edge(gls_clk) then
            case state_wb is
                when init_wb =>
                    transmission    <= '0';
                    reception       <= '0';
                    if (wbs_strobe and wbs_write) = '1' then
                        state_wb <= write_register;
                    elsif (wbs_strobe = '1') and (wbs_write = '0') then
                        state_wb <= read_register;
                    end if;
                when write_register =>
                    if wbs_strobe = '0' then
                        state_wb <= init_wb;
                    else
                        --ask for communication if a transmit is in progress or if the data is busy generate an error
                        if wbs_add(1 downto 0) = "01" then
                            if (wbs_writedata(1) or wbs_writedata(2)) = '1' and (not anybus_interface_busy or com_in_progress) = '1' then
                                state_wb <= transmission_error;
                                communication_error <= '1';
                            else
                                transmission <= wbs_writedata(1);
                                reception <= wbs_writedata(2);
                            end if;
                            wait_clock_cycles <= to_integer(unsigned(wbs_writedata(5 downto 3)));
                        elsif wbs_add(1 downto 0) = "10" then
                            ADDRESS_REG(11 downto 0) <= wbs_writedata(11 downto 0);
                        elsif wbs_add(1 downto 0) = "11" then
                            DATA_WRITE_REG(7 downto 0) <= wbs_writedata(7 downto 0);
                        end if;
                    end if;
                when read_register =>
                    if wbs_add(1 downto 0) = "11" and com_in_progress = '1' then
                        communication_error <= '1';
                        state_wb <= transmission_error;
                    end if;
                    if wbs_strobe = '0' then
                        state_wb <= init_wb;
                        --Read in the CONTROL_REG will clear error flag
                        if wbs_add(1 downto 0) = "01"  then
                            communication_error <= '0';
                        end if;
                    end if;
                when transmission_error =>
                    if wbs_strobe = '0' then
                        state_wb <= init_wb;
                    end if;
            end case;
        end if;
    end process fsm_wb_interface;

    --FSM of the Anybus interface
    fsm_anybus : process(gls_clk, gls_reset)
        variable counter : integer range 0 to 7;
        begin
        if gls_reset = '1' then
            --Return to the waiting state
            state_anybus <= init_anybus;
            counter := 0;
            com_in_progress <= '0';
            message_data <= (others => '0');
            message_addr <= (others => '0');
            DATA_READ_REG <= (others => '0');
        elsif rising_edge(gls_clk) then
            case state_anybus is
                when init_anybus =>
                    counter := 0;
                    com_in_progress <= '0';
                    if (communication_error = '0' and (CONTROL_REG(1) or CONTROL_REG(2)) = '1') then
                        state_anybus <= start;
                    end if;
                    message_data <= DATA_WRITE_REG(7 downto 0);
                    message_addr <= ADDRESS_REG(11 downto 0);
                when start =>
                    com_in_progress <= '1';
                    if CONTROL_REG(1) = '1' then
                        state_anybus <= write;
                    elsif CONTROL_REG(2) = '1' then
                        state_anybus <= read;
                    end if;
                --Write
                when write =>
                    if counter + 1 < wait_clock_cycles then
                        counter := counter + 1;
                    else
                        state_anybus <= end_write;
                    end if;
                when end_write =>
                    state_anybus <= init_anybus;
                --read
                when read =>
                    if counter + 1 < wait_clock_cycles then
                        counter := counter + 1;
                    else
                        state_anybus <= end_read;
                    end if;
                    DATA_READ_REG(7 downto 0) <= anybus_interface_data;
                when end_read =>
                    state_anybus <= init_anybus;
                    DATA_READ_REG(7 downto 0) <= anybus_interface_data;
                when others =>
                    state_anybus <= init_anybus;
            end case;
        end if;
    end process fsm_anybus;

    --Anybus IO interface
    anybus_interface_addr(10 downto 0)    <= message_addr(10 downto 0);
    anybus_interface_addr(11)             <= '1';
    anybus_interface_data     <=  message_data(7 downto 0) when state_anybus = write or state_anybus = end_write else
                            (others => 'Z');
    anybus_interface_oe       <=  '0' when state_anybus = read or state_anybus = end_read else
                            '1';
    anybus_interface_rw       <=  '0' when state_anybus = write else
                            '1';
    anybus_interface_ce       <=  '1' when state_anybus = init_anybus or state_anybus = end_read else
                            '0';

    --Wishbone interface
    CONTROL_REG(0)  <= communication_error;
    CONTROL_REG(1)  <= transmission;
    CONTROL_REG(2)  <= reception;
    CONTROL_REG(5 downto 3) <= std_logic_vector(to_unsigned(wait_clock_cycles,3));
    CONTROL_REG(15 downto 6) <= (others => '0');
    wbs_readdata(wb_size-1 downto 0) <= std_logic_vector(to_unsigned(ID, wb_size)) when wbs_add = "00" else
                                        CONTROL_REG when wbs_add = "01" else
                                        ADDRESS_REG when wbs_add = "10" else
                                        DATA_READ_REG when wbs_add = "11" and com_in_progress = '0' else
                                        (others => '0');
    wbs_ack     <=  '1' when state_wb = read_register or state_wb = write_register else
                    '0';

end architecture anybus_interface_arch;


