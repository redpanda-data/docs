package main

import (
	"log"
	"os"
	"regexp"
	"strings"

	"github.com/redpanda-data/redpanda/src/transform-sdk/go/transform"
)

var (
	re         *regexp.Regexp
	checkValue bool
)

func isTrueVar(v string) bool {
	switch strings.ToLower(v) {
	case "yes", "ok", "1", "true":
		return true
	default:
		return false
	}
}

// Runs only once at startup
func main() {
	// Set logging preferences, including timestamp and UTC time
	log.SetPrefix("[regex-transform] ")
	log.SetFlags(log.Ldate | log.Ltime | log.LUTC | log.Lmicroseconds)

	// Start logging the transformation process
	log.Println("Starting transform...")

	// Read the PATTERN environment variable to get the regex pattern
	pattern, ok := os.LookupEnv("PATTERN")
	if !ok {
		log.Fatal("Missing PATTERN environment variable")
	}
	// Log the pattern being used
	log.Printf("Using PATTERN: %q\n", pattern)
	// Compile the regex pattern for later use
	re = regexp.MustCompile(pattern)

	// Read the MATCH_VALUE environment variable to determine whether to check the record's value
	mk, ok := os.LookupEnv("MATCH_VALUE")
	checkValue = ok && isTrueVar(mk)
	log.Printf("MATCH_VALUE set to: %t\n", checkValue)

	log.Println("Initialization complete, waiting for records...")

	// Listen for records to be written, calling doRegexFilter for each record
	transform.OnRecordWritten(doRegexFilter)
}

// doRegexFilter is the function that applies the regex filter to each incoming record.
func doRegexFilter(e transform.WriteEvent, w transform.RecordWriter) error {
	// This stores the data to be checked (either the key or value)
	var dataToCheck []byte

	// Depending on the MATCH_VALUE environment variable, decide whether to check the record's key or value
	if checkValue {
		// Use the value of the record if MATCH_VALUE is true
		dataToCheck = e.Record().Value
		log.Printf("Checking record value: %s\n", string(dataToCheck))
	} else {
		// Use the key of the record if MATCH_VALUE is false
		dataToCheck = e.Record().Key
		log.Printf("Checking record key: %s\n", string(dataToCheck))
	}

	// If there is no key or value to check, log and skip the record
	if dataToCheck == nil {
		log.Println("Record has no key/value to check, skipping.")
		return nil
	}

	// Check if the data matches the regex pattern
	pass := re.Match(dataToCheck)
	if pass {
		// If the record matches the pattern, log and write the record to the output topic
		log.Printf("Record matched pattern, passing through. Key: %s, Value: %s\n", string(e.Record().Key), string(e.Record().Value))
		return w.Write(e.Record())
	} else {
		// If the record does not match the pattern, log and drop the record
		log.Printf("Record did not match pattern, dropping. Key: %s, Value: %s\n", string(e.Record().Key), string(e.Record().Value))
		// Do not write the record if it doesn't match
		return nil
	}
}