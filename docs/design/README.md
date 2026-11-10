# Design Models

The models of the [Software Design Report](../software_design_report.md). Each diagram has a Mermaid source (`.mmd`) and PNG/SVG exports.

| Model | Files | Report section |
|---|---|---|
| Layered architecture | [png](arch/layered_architecture.png), [svg](arch/layered_architecture.svg), [mmd](arch/layered_architecture.mmd) | 3.1 |
| Deployment | [png](arch/deployment.png), [svg](arch/deployment.svg), [mmd](arch/deployment.mmd) | 3.3 |
| Domain classes | [png](class/domain_classes.png), [svg](class/domain_classes.svg), [mmd](class/domain_classes.mmd) | 4.1 |
| Services, repositories, infrastructure | [png](class/service_layer.png), [svg](class/service_layer.svg), [mmd](class/service_layer.mmd) | 4.2 |
| Sequence UC-01 register and verify | [png](sequence/uc01_register_and_verify.png), [mmd](sequence/uc01_register_and_verify.mmd) | 5.1 |
| Sequence UC-02 log in | [png](sequence/uc02_login.png), [mmd](sequence/uc02_login.mmd) | 5.2 |
| Sequence UC-04, UC-07 create event | [png](sequence/uc04_uc07_create_event.png), [mmd](sequence/uc04_uc07_create_event.mmd) | 5.3 |
| Sequence UC-05, UC-06 browse and join | [png](sequence/uc05_uc06_browse_and_join.png), [mmd](sequence/uc05_uc06_browse_and_join.mmd) | 5.4 |
| Sequence UC-08 manage facility schedule | [png](sequence/uc08_manage_facility_schedule.png), [mmd](sequence/uc08_manage_facility_schedule.mmd) | 5.5 |
| Sequence UC-10, UC-11 leave and cancel | [png](sequence/uc10_uc11_leave_and_cancel.png), [mmd](sequence/uc10_uc11_leave_and_cancel.mmd) | 5.6 |

Sequence diagrams cover 9 of 11 use cases (82 %; required: at least 30 %).

Render a diagram: `npx -p @mermaid-js/mermaid-cli mmdc -i arch/layered_architecture.mmd -o arch/layered_architecture.png -s 2 -b white`
