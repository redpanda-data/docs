package main
// This data transform filters records based on a customizable regex pattern.
// If a record's key or value
// (determined by an environment variable) matches the specified regex,
// the record is forwarded to the output.
// Otherwise, it is dropped.
//
// Usage:
// 1. Provide the following environment variables in your Docker or configuration setup:
//    - PATTERN     : (required) a regular expression that determines what you want to match.
//    - MATCH_VALUE : (optional) a boolean to decide whether to check the record value. If false,
//                   the record key is checked. Default is false.
//
// Example environment variables:
//   PATTERN=".*\\.edu$"
//   MATCH_VALUE="true"
//
// Logs:
// This transform logs information about each record and whether it matched.
// The logs appear in the _redpanda.transform_logs topic, so you can debug how your records are being processed.
//
// Build instructions:
//   go mod tidy
//   rpk transform build
//
// For more details on building transforms with the Redpanda SDK, see:
// https://docs.redpanda.com/current/develop/data-transforms
//

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

// The main() function runs only once at startup. It performs all initialization steps:
// - Reads and compiles the regex pattern.
// - Determines whether to match on the key or value.
// - Registers the doRegexFilter() function to process records.
func main() {
	// Set logging preferences, including timestamp and UTC time.
	log.SetPrefix("[regex-transform] ")
	log.SetFlags(log.Ldate | log.Ltime | log.LUTC | log.Lmicroseconds)

	// Start logging the transformation process
	log.Println("Starting transform...")

	// Read the PATTERN environment variable to get the regex pattern.
	pattern, ok := os.LookupEnv("PATTERN")
	if !ok {
		log.Fatal("Missing PATTERN environment variable")
	}
	// Log the regex pattern being used.
	log.Printf("Using PATTERN: %q\n", pattern)
	// Compile the regex pattern for later use.
	re = regexp.MustCompile(pattern)

	// Read the MATCH_VALUE environment variable to determine whether to check the record's value.
	mk, ok := os.LookupEnv("MATCH_VALUE")
	checkValue = ok && isTrueVar(mk)
	log.Printf("MATCH_VALUE set to: %t\n", checkValue)

	log.Println("Initialization complete, waiting for records...")

	// Listen for records to be written, calling doRegexFilter() for each record.
	transform.OnRecordWritten(doRegexFilter)
}

// The doRegexFilter() function executes each time a new record is written.
// It checks whether the record's key or value (based on MATCH_VALUE) matches the compiled regex.
// If it matches, the record is forwarded, if not, it's dropped.
func doRegexFilter(e transform.WriteEvent, w transform.RecordWriter) error {
	// This stores the data to be checked (either the key or value).
	var dataToCheck []byte

	// Depending on the MATCH_VALUE environment variable, decide whether to check the record's key or value.
	if checkValue {
		// Use the value of the record if MATCH_VALUE is true.
		dataToCheck = e.Record().Value
		log.Printf("Checking record value: %s\n", string(dataToCheck))
	} else {
		// Use the key of the record if MATCH_VALUE is false.
		dataToCheck = e.Record().Key
		log.Printf("Checking record key: %s\n", string(dataToCheck))
	}

	// If there is no key or value to check, log and skip the record.
	if dataToCheck == nil {
		log.Println("Record has no key/value to check, skipping.")
		return nil
	}

	// Check if the data matches the regex pattern.
	pass := re.Match(dataToCheck)
	if pass {
		// If the record matches the pattern, log and write the record to the output topic.
		log.Printf("Record matched pattern, passing through. Key: %s, Value: %s\n", string(e.Record().Key), string(e.Record().Value))
		return w.Write(e.Record())
	} else {
		// If the record does not match the pattern, log and drop the record.
		log.Printf("Record did not match pattern, dropping. Key: %s, Value: %s\n", string(e.Record().Key), string(e.Record().Value))
		// Do not write the record if it doesn't match the pattern.
		return nil
	}
}