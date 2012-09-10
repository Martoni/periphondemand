library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.ALL;

-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity pod_pwm is
    generic (
        id : natural := 1;
        wb_size : natural := 16
    );
    port(
        gls_reset : in std_logic;
        gls_clk : in std_logic;
        wbs_add : in std_logic_vector(1 downto 0);
        wbs_writedata : in std_logic_vector(wb_size-1 downto 0);
        wbs_readdata : out std_logic_vector(wb_size-1 downto 0);
        wbs_strobe : in std_logic;
        wbs_cycle : in std_logic;
        wbs_write : in std_logic;
        wbs_ack : out std_logic;
        pwm_output : out std_logic
    );
end pod_pwm;

architecture Behavioral of pod_pwm is
    type state_wb_type is (init_wb, write_register, read_register);
    signal state_wb : state_wb_type := init_wb;
    signal t_on : std_logic_vector(wb_size-1 downto 0);
    signal div : std_logic_vector(wb_size-1 downto 0);
begin

    wb_interface : process(gls_clk, gls_reset)
    begin
        if gls_reset = '1' then
            state_wb <= init_wb;
            t_on <= (others => '0');
            div <= (others => '0');
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
                        if wbs_add = "01" then
                            t_on <= wbs_writedata(wb_size-1 downto 0);
                        elsif wbs_add = "10" then
                            div <= wbs_writedata(wb_size-1 downto 0);
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
    end process;

    pwm_generation : process(gls_clk)
        variable cpt : integer range 0 to 65535 := 0;
    begin
        if rising_edge(gls_clk) then

            if cpt < to_integer(unsigned(div))-1 then
                if cpt < to_integer(unsigned(t_on)) then
                    pwm_output <= '1';
                else
                    pwm_output <= '0';
                end if;

                cpt := cpt + 1;
            else
                pwm_output <= '0';
                cpt := 0;
            end if;
        end if;
    end process;

    wbs_readdata(wb_size-1 downto 0) <= std_logic_vector(to_unsigned(id, wb_size)) when wbs_add = "00" else
                                          t_on  when wbs_add = "01" else
                                          div   when wbs_add = "10" else
                                          (others => '0');

end Behavioral;
