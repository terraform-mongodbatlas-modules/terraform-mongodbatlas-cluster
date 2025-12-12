package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/hashicorp/go-changelog"
)

var (
	allowedTypeValues          = getValidValues("../allowed-types.txt")
	allowedPrefixValues        = getValidValues("../allowed-prefixes.txt")
	typesRequireResourcePrefix = []string{"breaking-change", "enhancement", "bug"}
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: go run main.go <path-to-changelog-file>")
	}

	filePath := os.Args[1]
	content, err := os.ReadFile(filePath)
	if err != nil {
		// If file doesn't exist, that's ok - not all PRs require changelog entries
		if os.IsNotExist(err) {
			fmt.Printf("No changelog entry file found at: %s (this may be expected)\n", filePath)
			return
		}
		log.Fatalf("Error reading changelog file %s: %v", filePath, err)
	}

	validateChangelog(string(content))
}

func validateChangelog(body string) {
	entry := changelog.Entry{
		Body: body,
	}
	// grabbing validation logic from https://github.com/hashicorp/go-changelog/blob/main/entry.go#L66, if entry types become configurable we can invoke entry.Validate() directly
	notes := changelog.NotesFromEntry(entry)

	if len(notes) < 1 {
		log.Fatal("Error validating changelog: no changelog entry found")
	}

	var unknownTypes []string
	for _, note := range notes {
		if !containsType(note.Type, allowedTypeValues) {
			unknownTypes = append(unknownTypes, note.Type)
		}
	}
	if len(unknownTypes) > 0 {
		log.Fatalf("Error validating changelog: Unknown changelog types %v, please use only the configured changelog entry types %v", unknownTypes, allowedTypeValues)
	}

	validateEntryPrefix(notes)
	fmt.Println("Changelog entry is valid")
}

func validateEntryPrefix(entries []changelog.Note) {
	for _, entry := range entries {
		entryContent := entry.Body
		if containsType(entry.Type, typesRequireResourcePrefix) {
			hasValidPrefix := false
			for _, prefix := range allowedPrefixValues {
				if strings.HasPrefix(entryContent, prefix) {
					hasValidPrefix = true
					break
				}
			}
			if !hasValidPrefix {
				log.Fatalf("Error validating changelog: An incorrect prefix was found in the definition of the changelog entry. Please use one of the allowed prefixes: %v", allowedPrefixValues)
			}
		}
	}
}

func containsType(entryType string, allowed []string) bool {
	for _, a := range allowed {
		if a == entryType {
			return true
		}
	}
	return false
}

func getValidValues(path string) []string {
	content, errFile := os.ReadFile(path)
	if errFile != nil {
		log.Fatalf("Error reading allowed values from %s: %v", path, errFile)
	}
	lines := strings.Split(string(content), "\n")
	// Filter out empty lines
	var validValues []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line != "" {
			validValues = append(validValues, line)
		}
	}
	return validValues
}
