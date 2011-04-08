---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 16/04/2008
-- File          : i2cocore_wb16.vhd
--
-- Abstract : A wrapper to include i2c open cores in
-- a 16bits data wishbone bus
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity i2cocore is
---------------------------------------------------------------------------
generic(
    id : natural := 1;
    wb_size : natural := 16
);
port
(
	clk_i : in std_logic ; -- master clock input
	rst_i : in std_logic ; -- asynchronous reset

	adr_i : in std_logic_vector( 3 downto 0);
	dat_i : in std_logic_vector( 15 downto 0);
	dat_o : out std_logic_vector( 15 downto 0);
	we_i  : in std_logic ;
	stb_i : in std_logic ;
	ack_o : out std_logic ;
    cyc_i : in std_logic;

	inta_o: out std_logic ;

	scl : inout std_logic ;
	sda : inout std_logic
);
end entity i2cocore;


---------------------------------------------------------------------------
Architecture i2cocore_1 of i2cocore is
---------------------------------------------------------------------------
	component wishbone_i2c_master
		port (
		-- wishbone signals
	 CLK_I  : in std_logic;				-- master clock input
	 RST_I  : in std_logic := '0';			-- synchronous active high reset
	 nRESET : in std_logic := '1';			-- asynchronous active low reset
	 ADR_I  : in std_logic_vector(1 downto 0);		-- lower address bits
	 DAT_I  : in std_logic_vector(15 downto 0);	-- Databus input
	 DAT_O  : out std_logic_vector(15 downto 0);	-- Databus output
	 SEL_I  : in std_logic_vector(1 downto 0);		-- Byte select signals
	 WE_I   : in std_logic;				-- Write enable input
	 STB_I  : in std_logic;				-- Strobe signals / core select signal
	 CYC_I  : in std_logic;				-- Valid bus cycle input
	 ACK_O  : out std_logic;			-- Bus cycle acknowledge output
	 INTA_O : out std_logic;			-- interrupt request output signal

		-- I2C signals
	 SCLi   : in std_logic;				-- I2C clock line
	 SCLo   : out std_logic;
	 SDAi   : in std_logic;				-- I2C data line
	 SDAo   : out std_logic
				 );
	end component;

	signal SCLi : std_logic ;
	signal SCLo : std_logic ;
	signal SDAi : std_logic ;
	signal SDAo : std_logic ;

	signal dataI : std_logic_vector( 15 downto 0);
	signal dataO : std_logic_vector( 15 downto 0);
	signal sel : std_logic_vector( 1 downto 0);
	signal rst : std_logic ;

    signal strobe : std_logic ;

begin


	connect_wishbone_i2c_master : wishbone_i2c_master
	port map (
					 -- wishbone signals
						 CLK_I  => clk_i,	-- master clock input
						 RST_I  => '0',		-- synchronous active high reset
						 NRESET => rst,		-- asynchronous active low reset
						 ADR_I  => adr_i(2 downto 1),	-- lower address bits
						 DAT_I  => dataI,	-- Databus input
						 DAT_O  => dataO,	-- Databus output
						 SEL_I  => sel,		-- Byte select signals
						 WE_I   => we_i,	-- Write enable input
						 STB_I  => strobe,	-- Strobe signals/
                                            -- core select signal
						 CYC_I  => cyc_i,	-- Valid bus cycle input
						 ACK_O  => ack_o,	-- Bus cycle acknowledge output
						 INTA_O => inta_o,	-- interrupt request output signal

					 -- I2C signals
						 SCLi   => SCLi,	-- I2C clock line
						 SCLo   => SCLo,
						 SDAi   => SDAi,	-- I2C data line
						 SDAo   => SDAo
		);

	rst <= not rst_i;

    -- controls
    strobe <=  stb_i when adr_i(3) = '0' else '0';
	sel <= "01" when (adr_i(0) = '0') else "10";

    -- write data
    write_p : process (adr_i(0))
    begin
        if (adr_i(0) = '0') then
        	dataI <= "00000000"&dat_i(7 downto 0);
        else
		    dataI <= dat_i(7 downto 0)&"00000000";
        end if;
    end process write_p;

    -- read data
    read_p : process (adr_i, stb_i)
    begin
        if stb_i = '1' then
            if (adr_i(3) = '1')  then
                dat_o <= std_logic_vector( to_unsigned(id,wb_size));
            elsif (adr_i(0) = '0') then
                dat_o <= "00000000"&dataO(7 downto 0);
            else
                dat_o <= "00000000"&dataO(15 downto 8);
            end if;
        else
            dat_o <= (others => '0');
        end if;
    end process read_p;


    -- I2C bus
	scl <= '0' when (SCLo = '0') else 'Z';
	sda <= '0' when (SDAo = '0') else 'Z';
	SCLi <= scl;
	SDAi <= sda;

end architecture i2cocore_1;

