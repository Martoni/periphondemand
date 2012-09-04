--
-- Copyright (c) ARMadeus Project 2011
--
-- servo driving
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
-- File          : servo.vhd
-- Created on    : 2/02/2012
-- Author        : Kevin JOLY joly.kevin25@gmail.com
--
--*********************************************************************
library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

entity pod_servo is
    generic (
        id : natural := 1;
        wb_size : natural := 16
    );
    port (
        -- Syscon signals
        gls_reset           : in std_logic;
        gls_clk             : in std_logic;
        -- Wishbone signals
        wbs_add             : in std_logic;
        wbs_writedata       : in std_logic_vector( wb_size-1 downto 0);
        wbs_readdata        : out std_logic_vector( wb_size-1 downto 0);
        wbs_strobe          : in std_logic;
        wbs_cycle           : in std_logic;
        wbs_write           : in std_logic;
        wbs_ack             : out std_logic;
        --Servo output signal
        pwm_output     : out std_logic
    );
end entity pod_servo;

architecture servo_arch of pod_servo is
    --state signal for Wisbone
    type state_wb_type is (init_wb, write_register, read_register);
    signal state_wb : state_wb_type := init_wb;
    --State signal for servo_process
    signal angle  : integer range 0 to 1000 := 500;
    signal enable_servo : std_logic;
begin
    --FSM of the Wishbone interface
    fsm_wb_interface : process(gls_clk, gls_reset)
    begin
        if gls_reset = '1' then
            --Return to the waiting state
            state_wb            <= init_wb;
            angle               <= 500;
        elsif rising_edge(gls_clk) then
            case state_wb is
                when init_wb =>
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
                        if wbs_add = '1' then
                            if (to_integer(unsigned(wbs_writedata(10 downto 0))) > 1000) then
                                angle <= 1000;
                            else
                                angle <= to_integer(unsigned(wbs_writedata(10 downto 0)));
                            end if;
                        end if;
                    end if;
                when read_register =>
                    if wbs_strobe = '0' then
                        state_wb <= init_wb;
                    end if;
                when others =>
                    state_wb <= init_wb;
            end case;
        end if;
    end process fsm_wb_interface;

    servo_process : process(gls_clk, gls_reset)
    variable counter : integer range 0 to 20000 := 0;
    begin
        if gls_reset = '1' then
            counter := 0;
            pwm_output <= '0';
        elsif rising_edge(gls_clk) then
            if enable_servo = '1' then
                if counter < (angle + 1000) then
                    counter := counter + 1;
                    pwm_output <= '1';
                elsif counter < (20000 - (angle + 1000)) then
                    counter := counter + 1;
                    pwm_output <= '0';
                else
                    counter := 0;
                    pwm_output <= '1';
                end if;
            end if;
        end if;
    end process servo_process;

    --Generate the enable_servo with a period of 1us
    divider_process : process(gls_clk, gls_reset)
    variable counter : integer range 0 to 100 := 0;
    begin
        if gls_reset = '1' then
            counter := 0;
            enable_servo <= '0';
        elsif rising_edge(gls_clk) then
            if counter < 99 then
                counter := counter + 1;
                enable_servo <= '0';
            else
                enable_servo <= '1';
                counter := 0;
            end if;
        end if;
    end process divider_process;

    wbs_readdata(wb_size-1 downto 0) <= std_logic_vector(to_unsigned(id, wb_size))      when wbs_add = '0' else
                                        std_logic_vector(to_unsigned(angle, wb_size))   when wbs_add = '1' else
                                        (others => '0');

    wbs_ack     <=  '1' when state_wb = read_register or state_wb = write_register else
                    '0';

end architecture servo_arch;


