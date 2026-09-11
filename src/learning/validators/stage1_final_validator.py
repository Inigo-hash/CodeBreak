"""
Validates the final Stage 1 coding challenge.

This challenge combines the beginner concepts learned
throughout the Island stage.
"""

import ast


class Stage1FinalValidator:

    def validate(self, challenge, tree):

        # -----------------------------------------------------
        # 1. Required variables
        # -----------------------------------------------------

        assigned_names = set()

        for node in ast.walk(tree):

            if isinstance(node, ast.Assign):

                for target in node.targets:

                    if isinstance(target, ast.Name):
                        assigned_names.add(target.id)

            elif isinstance(node, ast.AugAssign):

                if isinstance(node.target, ast.Name):
                    assigned_names.add(node.target.id)

        required_names = {
            "name",
            "score_text",
            "score",
            "rank",
            "message",
            "final_message",
        }

        missing = required_names - assigned_names

        if missing:
            return False, (
                "Create all required variables: "
                + ", ".join(sorted(missing))
                + "."
            )

        # -----------------------------------------------------
        # 2. Check input()
        # -----------------------------------------------------

        input_targets = set()

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):

                for child in ast.walk(node.value):

                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id == "input"
                    ):

                        input_targets.add(
                            node.targets[0].id
                        )

        if "name" not in input_targets:
            return False, (
                "Use input() to store the explorer name in name."
            )

        if "score_text" not in input_targets:
            return False, (
                "Use input() to store the score in score_text."
            )

        # -----------------------------------------------------
        # 3. Check int(score_text)
        # -----------------------------------------------------

        casting_found = False

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "score"
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "int"
                and len(node.value.args) == 1
                and isinstance(node.value.args[0], ast.Name)
                and node.value.args[0].id == "score_text"
            ):

                casting_found = True
                break

        if not casting_found:

            return False, (
                "Convert score_text using int() "
                "and store it in score."
            )

        # -----------------------------------------------------
        # 4. Check score += 10
        # -----------------------------------------------------

        operator_found = False

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.AugAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "score"
                and isinstance(node.op, ast.Add)
                and isinstance(node.value, ast.Constant)
                and node.value.value == 10
            ):

                operator_found = True
                break

        if not operator_found:

            return False, (
                "Add 10 to score using +=."
            )

        # -----------------------------------------------------
        # 5. Check if / elif / else exists
        # -----------------------------------------------------

        if_node = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.If)
            ),
            None,
        )

        if if_node is None:

            return False, (
                "Use an if/elif/else statement "
                "to decide the rank."
            )

        has_elif = (
            len(if_node.orelse) == 1
            and isinstance(if_node.orelse[0], ast.If)
        )

        if not has_elif:

            return False, (
                "Add the required elif condition."
            )

        elif_node = if_node.orelse[0]

        if not elif_node.orelse:

            return False, (
                "Finish the rank decision with else."
            )

        # -----------------------------------------------------
        # 6. Check f-string assigned to message
        # -----------------------------------------------------

        formatted_output_found = False

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "message"
                and isinstance(node.value, ast.JoinedStr)
            ):

                formatted_output_found = True
                break

        if not formatted_output_found:

            return False, (
                "Create message using an f-string."
            )

        # -----------------------------------------------------
        # 7. Check message.upper()
        # -----------------------------------------------------

        upper_found = False

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "final_message"
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "upper"
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "message"
            ):

                upper_found = True
                break

        if not upper_found:

            return False, (
                "Create final_message using message.upper()."
            )

        # -----------------------------------------------------
        # 8. Check print(final_message)
        # -----------------------------------------------------

        print_found = False

        for node in ast.walk(tree):

            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "final_message"
            ):

                print_found = True
                break

        if not print_found:

            return False, (
                "Print final_message."
            )

        return True, (
            "Excellent! You applied the Stage 1 "
            "Python concepts correctly."
        )