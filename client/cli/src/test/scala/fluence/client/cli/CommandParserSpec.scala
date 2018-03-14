/*
 * Copyright (C) 2017  Fluence Labs Limited
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

package fluence.client.cli

import fluence.client.cli.CliOp._
import org.scalatest.{ Matchers, WordSpec }

class CommandParserSpec extends WordSpec with Matchers {

  //todo test with escape characters
  "command parser" should {
    "parse all commands correctly" in {
      CommandParser.parseCommand("exit and some '\" other string").get shouldBe Exit
      CommandParser.parseCommand("exit").get shouldBe Exit

      val key = "somekey"
      val value = "somevalue"
      CommandParser.parseCommand(s"""put $key $value""").get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put '$key' '$value' """).get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put '$key' $value """).get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put '$key' "$value" """).get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put $key "$value" """).get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put "$key" "$value" """).get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put "$key" $value""").get shouldBe Put(key, value)
      CommandParser.parseCommand(s"""put "$key" '$value'""").get shouldBe Put(key, value)

      CommandParser.parseCommand(s"""get $key """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get '$key' """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get '$key'  """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get '$key'  """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get $key  """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get "$key"  """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get "$key" """).get shouldBe Get(key)
      CommandParser.parseCommand(s"""get "$key" """).get shouldBe Get(key)
    }
  }

}