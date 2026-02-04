# Supplier Research Prompt

Use this prompt in a separate Claude session to identify key suppliers for each service category.

---

## Purpose

Provide **factual supplier names only** - the research system will discover buyer triggers, evaluation criteria, and market dynamics through web research.

**DO provide**: Vendor/supplier names (factual, can be verified)
**DO NOT provide**: Buyer triggers, evaluation criteria, typical buyers (research discovers these)

---

## Instructions

For each service category, identify 5-8 major vendors that enterprise buyers (500+ employees) typically evaluate. Focus on:
- Gartner Magic Quadrant leaders and notable challengers
- US market presence
- Current as of 2026

---

## Service Categories

### Category 1: Network Security

```yaml
security:
  name: "Network Security"
  subcategories:
    - "EDR (endpoint detection and response)"
    - "MDR (managed detection and response)"
    - "IAM (identity and access management)"
    - "SASE (secure access service edge)"
    - "ZTNA (zero trust network access)"
    - "CSPM (cloud security posture management)"
  key_suppliers:
    # List 5-8 major security vendors
    # Examples: Palo Alto Networks, CrowdStrike, Zscaler, Okta, Microsoft, SentinelOne, Fortinet
    - ""
```

### Category 2: Customer Experience (CX)

```yaml
customer_experience:
  name: "Customer Experience (CX)"
  subcategories:
    - "CCaaS (cloud contact center)"
    - "Omnichannel engagement (voice, chat, email, SMS)"
    - "AI virtual agents and chatbots"
    - "Workforce optimization"
  key_suppliers:
    # List 5-8 major CCaaS/CX vendors
    # Examples: Five9, Genesys, NICE, Talkdesk, Amazon Connect, Cisco, Vonage
    - ""
```

### Category 3: Network & Connectivity

```yaml
network:
  name: "Network & Connectivity"
  subcategories:
    - "Dedicated Internet Access (DIA)"
    - "MPLS and Ethernet services"
    - "SD-WAN (software-defined WAN)"
    - "Cloud direct connects"
    - "Fixed wireless"
  key_suppliers:
    # List 5-8 major carriers and network vendors
    # Examples: AT&T, Verizon, Lumen, Comcast Business, Cradlepoint, Fortinet, VMware
    - ""
```

### Category 4: Data Center & Colocation

```yaml
data_center:
  name: "Data Center & Colocation"
  subcategories:
    - "Colocation (cabinet space, power, cooling)"
    - "Interconnection services"
    - "Edge computing infrastructure"
  key_suppliers:
    # List 5-8 major colocation providers
    # Examples: Equinix, Digital Realty, CyrusOne, QTS, CoreSite, DataBank, Flexential
    - ""
```

### Category 5: Communications & Voice

```yaml
communications:
  name: "Communications & Voice"
  subcategories:
    - "UCaaS (unified communications)"
    - "SIP trunking"
    - "Cloud PBX and hosted voice"
    - "Video conferencing"
  key_suppliers:
    # List 5-8 major UCaaS/voice vendors
    # Examples: Microsoft Teams, Zoom, RingCentral, 8x8, Vonage, Cisco Webex, Dialpad
    - ""
```

### Category 6: Cloud Infrastructure

```yaml
cloud:
  name: "Cloud Infrastructure"
  subcategories:
    - "Cloud strategy and migration"
    - "Multi-cloud architecture"
    - "AI/ML infrastructure"
  key_suppliers:
    # List 5-8 major cloud providers
    # Examples: AWS, Microsoft Azure, Google Cloud, Oracle Cloud, IBM Cloud
    - ""
```

---

## Sources to Consult

- Gartner Magic Quadrant (current year)
- Forrester Wave reports
- G2 Grid category leaders
- Recent analyst coverage

---

## Expected Output

YAML blocks with `key_suppliers` populated, ready to merge into `baseline.yaml`.

**Note**: The research system will discover buyer triggers, evaluation criteria, market pressures, and competitive dynamics through web research. You only need to provide supplier names.
