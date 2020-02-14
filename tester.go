package main

import (
	"bytes"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v2"
)

type testBlock struct {
	Name         string
	OsEnvEnabled bool   `yaml:"os_env,omitempty"`
	ExecSTRING   string `yaml:"execString"`
}

type testConfig struct {
	ConfigNAME string `yaml:"configName"`
	Tests      []testBlock
}

func getCwd() string {
	path, err := os.Getwd()
	if err != nil {
		log.Println(err)
	}
	return path
}

func runCommand(test testBlock, host string, path string, verbose bool) error {
	os.Chdir(filepath.Dir(path))
	cmd := exec.Command("bash", "-l", "-c", test.ExecSTRING)
	cmd.Env = append(os.Environ(), fmt.Sprintf("TARGET=%s", host))
	var stdOut bytes.Buffer
	var stdErr bytes.Buffer

	cmd.Stdout = &stdOut
	cmd.Stderr = &stdErr
	err := cmd.Run()
	if err != nil {
		log.Println("Test " + test.Name + " for target " + host + " : failed.")
		if verbose {
			log.Println("Output:\n" + stdErr.String() + "\n\n")
		}
	} else {
		log.Println("Test " + test.Name + " for target " + host + " : passed.")
		if verbose {
			log.Println("Output:\n" + stdOut.String() + "\n\n")
		}
	}
	return err
}

func runTests(hostList []string, tests testConfig, verbose bool) error {
	path := getCwd()
	allPassed := true
	for _, host := range hostList {
		for _, test := range tests.Tests {
			err := runCommand(test, host, path, verbose)
			if err != nil {
				allPassed = false
			}
		}
	}
	if allPassed == false {
		return errors.New("Not all tests passed")
	}
	return nil
}
func (c *testConfig) Parse(data []byte) error {
	if err := yaml.Unmarshal(data, c); err != nil {
		return err
	}
	if c.ConfigNAME == "" {
		return errors.New("'configName' cannot be empty")
	}

	for index, test := range c.Tests {
		if test.Name == "" {
			return errors.New("tests[" + string(index) + "][name] cannot be empty")
		}
		if test.ExecSTRING == "" {
			return errors.New("tests[" + string(index) + "][execString] cannot be empty")
		}

	}
	return nil
}

func main() {
	flag.Usage = func() {
		fmt.Printf("Usage of %s:\n", os.Args[0])
		fmt.Printf("    tester <testConfig.yaml> <targets.txt>\n")
		flag.PrintDefaults()
	}

	flag.Parse()
	if flag.NArg() == 0 {
		flag.Usage()
		os.Exit(1)
	}

	configData, configDataErr := ioutil.ReadFile(flag.Args()[0])
	if configDataErr != nil {
		log.Fatal(configDataErr)
	}

	hostData, hostDataErr := ioutil.ReadFile(flag.Args()[1])
	if hostDataErr != nil {
		log.Fatal(hostDataErr)
	}
	hostList := strings.Split(string(hostData), "\n")

	var config testConfig
	if parseErr := config.Parse(configData); parseErr != nil {
		log.Fatal(parseErr)
	}

	err := runTests(hostList, config, false)
	if err != nil {
		log.Fatal(err)
	}
}
